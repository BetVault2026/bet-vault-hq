BET VAULT HQ — CURRENT REPOSITORY NOTES

Repository: BetVault2026/bet-vault-hq
Default branch: main
Site type: static HTML, CSS and JavaScript. There is no build command.

PAGES AND DATA
- Homepage, bookmaker directory, football, boxing, tennis, guides, about/contact and legal pages are in the repository root.
- Football data refresh: Monday 06:05 UTC. Current GitHub Actions run succeeded on 23 November 2026.
- Boxing data refresh: Wednesday 06:25 UTC. Latest observed run succeeded on 23 November 2026.
- Tennis data refresh: Friday 11:15 UTC. The API fetch step succeeded on 23 November 2026, but the cache commit failed because the workflow pushed without first rebasing against main. The workflow has now been corrected to pull --rebase before pushing.
- Sports feeds can be incomplete or delayed. Verify data source terms and attribution before commercial use.

DEPLOYMENT
- No Cloudflare Pages deployment workflow is present in this repository.
- Earlier setup notes referred to Netlify, not Cloudflare. Confirm the actual hosting provider and connected project in its dashboard before assuming a push deploys the public site.
- Do not claim publication until a successful production deployment and public URL check are recorded.

BEFORE COMMERCIAL LAUNCH
- Complete and verify the publisher identity and contact details in the legal pages.
- Tailor privacy and cookie notices to the real form, email, hosting, analytics and payment processing configuration.
- Verify each bookmaker against the UK Gambling Commission public register and operator terms; do not invent ratings, current offers or affiliate relationships.
- Confirm permission/licensing for commercial reuse of third-party sports data.
- Complete a live test of membership submissions and Stripe payment links.
- Obtain appropriate review of gambling advertising, affiliate disclosures and applicable UK legal obligations.

CONTACT
Public contact email currently configured: betvault2026@protonmail.com
