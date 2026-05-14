#!/usr/bin/env python3
import argparse
import asyncio
import getpass
import json
import re
from pathlib import Path

from playwright.async_api import async_playwright


CHECK_TRUE_RE = re.compile(r"check\((\d+),\s*'true'\)")
CONFIG_FILE = Path(__file__).with_name("config.json")


def _load_config():
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


async def _attempt_cas_login(page, cas_username: str, cas_password: str, headless: bool):
    print("Attempting automatic CAS login...")
    try:
        await page.wait_for_selector(
            "input[name='username'], input#username, input[type='email'], input[name='login']",
            timeout=5000,
        )
    except Exception:
        print("CAS form not auto-detected.")
        if not headless:
            print("Browser is open. Please log in manually via CAS, then press Enter in this terminal.")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, input, "Press Enter after logging in...\n")
        return

    usr_sel = None
    for sel in ["input[name='username']", "input#username", "input[type='email']", "input[name='login']"]:
        try:
            await page.wait_for_selector(sel, timeout=500)
            usr_sel = sel
            break
        except Exception:
            continue

    pwd_sel = None
    for sel in ["input[name='password']", "input#password", "input[type='password']"]:
        try:
            await page.wait_for_selector(sel, timeout=500)
            pwd_sel = sel
            break
        except Exception:
            continue

    if usr_sel and pwd_sel:
        await page.fill(usr_sel, cas_username)
        await page.fill(pwd_sel, cas_password)
        try:
            await page.click("button[type='submit']", timeout=1000)
        except Exception:
            try:
                await page.click("input[type='submit']", timeout=1000)
            except Exception:
                await page.press(pwd_sel, "Enter")

        print("Identifiants envoyés, attente de redirection...")
        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass
    else:
        print("Username/password fields not detected.")
        if not headless:
            print("Please log in manually in the browser window, then press Enter in this terminal.")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, input, "Press Enter after logging in...\n")


async def _get_participants_frame(page, timeout: int):
    deadline = asyncio.get_event_loop().time() + (timeout / 1000)
    while asyncio.get_event_loop().time() < deadline:
        frame = page.frame(name="participants")
        if frame:
            return frame
        await asyncio.sleep(0.2)
    return None


async def _open_root_category(frame):
    await frame.evaluate(
        """
        (rootHref) => {
          const root = Array.from(document.querySelectorAll('a')).find(
            a => (a.getAttribute('href') || '').includes(rootHref)
          );
          if (root) root.click();
        }
        """,
        "openCategory('category7')",
    )


async def _collect_tree_resources(page, timeout: int, max_steps: int, click_delay_ms: int):
    frame = await _get_participants_frame(page, timeout)
    if not frame:
        raise RuntimeError("Frame 'participants' not found")

    await _open_root_category(frame)
    await page.wait_for_timeout(click_delay_ms)

    seen_branches = set()
    resources_by_id = {}

    for _ in range(max_steps):
        snapshot = await frame.evaluate(
            r"""
            () => {
              const lines = Array.from(document.querySelectorAll('div.treeline, div.treelineselected'));
              const openIds = [];
              const items = [];
              const stack = [];

              const depthFromLine = (line) => {
                const raw = line.innerHTML || '';
                const leading = (raw.match(/^(?:\s|&nbsp;|&#160;|\u00a0)*/i) || [''])[0];
                const nbspCount = (leading.match(/&nbsp;|&#160;|\u00a0/g) || []).length;
                return Math.floor(nbspCount / 3);
              };

              const labelFromLine = (line) => {
                const labelAnchor = line.querySelector('span.treeitem a, span.treebranch a, span.treecategory a');
                return ((labelAnchor ? labelAnchor.textContent : line.textContent) || '').trim();
              };

              for (const line of lines) {
                const depth = depthFromLine(line);
                const label = labelFromLine(line);

                while (stack.length > depth) {
                  stack.pop();
                }
                if (label) {
                  stack[depth] = label;
                  stack.length = depth + 1;
                }

                const openAnchor = Array.from(line.querySelectorAll('a')).find(
                  a => (a.getAttribute('href') || '').includes('openBranch(')
                );
                const leafAnchor = Array.from(line.querySelectorAll('a')).find(
                  a => {
                    const href = a.getAttribute('href') || '';
                    return href.includes('check(') && href.includes("'true'");
                  }
                );

                const openHref = openAnchor ? (openAnchor.getAttribute('href') || '') : '';
                const leafHref = leafAnchor ? (leafAnchor.getAttribute('href') || '') : '';

                const openMatch = openHref.match(/openBranch\((\d+)\)/);
                if (openMatch) {
                  openIds.push(openMatch[1]);
                }

                const leafMatch = leafHref.match(/check\((\d+),\s*'true'\)/);
                if (leafMatch) {
                  items.push({
                    resourceId: leafMatch[1],
                    href: leafHref,
                    text: label,
                    path: stack.slice(0, depth + 1).filter(Boolean).join(' / '),
                    depth,
                  });
                }
              }

              return {
                openIds: [...new Set(openIds)],
                items,
              };
            }
            """
        )

        for item in snapshot["items"]:
            rid = item["resourceId"]
            existing = resources_by_id.get(rid)
            if not existing or len(item["path"]) > len(existing["path"]):
                resources_by_id[rid] = item

        next_branch = next((branch_id for branch_id in snapshot["openIds"] if branch_id not in seen_branches), None)
        if not next_branch:
            break

        seen_branches.add(next_branch)
        await frame.evaluate(
            """
            (branchId) => {
              const direct = document.querySelector(`a[href*="openBranch(${branchId})"]`);
              const fallback = Array.from(document.querySelectorAll('a')).find(
                a => (a.getAttribute('href') || '').includes(`openBranch(${branchId})`)
              );
              const target = direct || fallback;
              if (target) target.click();
            }
            """,
            next_branch,
        )
        await page.wait_for_timeout(click_delay_ms)

    results = []
    for rid, item in resources_by_id.items():
        if not CHECK_TRUE_RE.search(item["href"]):
            continue
        results.append(
            {
                "resourceId": rid,
                "text": item["text"],
                "path": item["path"],
                "href": item["href"],
            }
        )

    results.sort(key=lambda item: (item["path"], item["text"], item["resourceId"]))
    return results


async def scrape(
    url: str,
    output: str,
    headless: bool = False,
    timeout: int = 15000,
    interactive_login: bool = True,
    cas_username: str = None,
    cas_password: str = None,
    max_steps: int = 1000,
    click_delay_ms: int = 800,
):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        page = await browser.new_page()
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="networkidle")

        if interactive_login:
            if cas_username and cas_password:
                await _attempt_cas_login(page, cas_username, cas_password, headless)
            elif headless:
                cas_username = input("CAS username: ")
                cas_password = getpass.getpass("CAS password: ")
                await _attempt_cas_login(page, cas_username, cas_password, headless)
            else:
                print("Browser is open. Please log in manually via CAS in the browser window.")
                print("When login is complete, press Enter in this terminal to continue.")
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, input, "Press Enter after logging in...\n")

        print("Traversing the schedule tree and collecting resourceIds...")
        results = await _collect_tree_resources(
            page,
            timeout=timeout,
            max_steps=max_steps,
            click_delay_ms=click_delay_ms,
        )
        await browser.close()

    outp = Path(output)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"Wrote {len(results)} leaf nodes to {output}")


def main():
    config_data = _load_config()
    parser = argparse.ArgumentParser(
        description="Scrape ADE tree by opening branches sequentially and extract resourceId from javascript:check(..., 'true') links"
    )
    parser.add_argument('--url', '-u', default=config_data.get('url', 'https://ade-consult.univ-artois.fr/jsp/standard/gui/interface.jsp'), help='Base ADE URL')
    parser.add_argument('--output', '-o', default='ade_exports.json', help='Output JSON file')
    parser.add_argument('--headless', dest='headless', action='store_true', default=False, help='Run in headless mode (no browser window)')
    parser.add_argument('--no-interactive-login', dest='interactive_login', action='store_false', help='Do not pause for manual CAS login')
    parser.add_argument('--cas-username', dest='cas_username', help='CAS username to use for automatic login')
    parser.add_argument('--cas-password', dest='cas_password', help='CAS password to use for automatic login (use with caution)')
    parser.add_argument('--timeout', type=int, default=15000, help='Selector wait timeout in ms')
    parser.add_argument('--max-steps', type=int, default=1000, help='Maximum number of openBranch clicks')
    parser.add_argument('--click-delay-ms', type=int, default=800, help='Delay between branch clicks in ms')
    args = parser.parse_args()

    asyncio.run(
        scrape(
            args.url,
            args.output,
            headless=args.headless,
            timeout=args.timeout,
            interactive_login=args.interactive_login,
            cas_username=args.cas_username,
            cas_password=args.cas_password,
            max_steps=args.max_steps,
            click_delay_ms=args.click_delay_ms,
        )
    )


if __name__ == '__main__':
    main()
