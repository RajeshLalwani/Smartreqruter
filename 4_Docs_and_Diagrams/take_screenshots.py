import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        def force_dark(page):
            return page.evaluate('''
                localStorage.setItem('sr-landing-theme', 'dark');
                localStorage.setItem('sv-theme', 'dark');
                document.documentElement.setAttribute('data-bs-theme', 'dark');
            ''')
        
        print('1. Landing Page')
        await page.goto('http://127.0.0.1:8000/')
        await force_dark(page)
        await page.wait_for_timeout(2000)
        await page.screenshot(path='screenshot_landing.png', full_page=True)

        print('2. Jobs Page')
        await page.goto('http://127.0.0.1:8000/jobs/')
        await force_dark(page)
        await page.wait_for_timeout(2000)
        await page.screenshot(path='screenshot_jobs.png', full_page=True)

        print('3. Register')
        await page.goto('http://127.0.0.1:8000/accounts/register/?type=candidate')
        await force_dark(page)
        await page.wait_for_timeout(1000)
        await page.screenshot(path='screenshot_register.png', full_page=True)
        
        await page.fill('input[name="first_name"]', 'Test')
        await page.fill('input[name="last_name"]', 'User')
        import random
        num = random.randint(10000, 99999)
        email = f'test_cand_{num}@example.com'
        await page.fill('input[name="email"]', email)
        await page.fill('input[name="password"]', 'SecurePass123!')
        await page.fill('input[name="password_confirm"]', 'SecurePass123!')
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)

        if 'login' in page.url:
            await page.fill('input[name="username"]', email)
            await page.fill('input[name="password"]', 'SecurePass123!')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)

        print('4. Candidate Dashboard')
        await page.goto('http://127.0.0.1:8000/dashboard/candidate/')
        await force_dark(page)
        await page.wait_for_timeout(2000)
        await page.screenshot(path='screenshot_candidate_dashboard.png', full_page=True)
        
        print('Logout')
        await page.goto('http://127.0.0.1:8000/accounts/logout/')
        await page.wait_for_timeout(1000)
        
        print('5. Register Recruiter')
        await page.goto('http://127.0.0.1:8000/accounts/register/?type=recruiter')
        await page.fill('input[name="first_name"]', 'Corp')
        await page.fill('input[name="last_name"]', 'Recruiter')
        email_rec = f'test_rec_{num}@example.com'
        await page.fill('input[name="email"]', email_rec)
        await page.fill('input[name="password"]', 'SecurePass123!')
        await page.fill('input[name="password_confirm"]', 'SecurePass123!')
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)
        
        if 'login' in page.url:
            await page.fill('input[name="username"]', email_rec)
            await page.fill('input[name="password"]', 'SecurePass123!')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)
            
        print('6. Recruiter Dashboard')
        await page.goto('http://127.0.0.1:8000/dashboard/recruiter/')
        await force_dark(page)
        await page.wait_for_timeout(2000)
        print('Taking Rec Dashboard Screenshot...')
        await page.screenshot(path='screenshot_recruiter_dashboard.png', full_page=True)
        
        await browser.close()
        print('Done.')

if __name__ == '__main__':
    asyncio.run(main())
