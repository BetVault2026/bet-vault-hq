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
- Hosting provider confirmed by the owner: Cloudflare.
- This repository has no Cloudflare deployment workflow file. Cloudflare Pages may deploy automatically if its Git integration is connected to this repository's main branch, but that connection and a production deployment have not been verified from the available GitHub access.
- Do not claim publication until the Cloudflare Pages project shows a successful production deployment and its public URL is checked.

BEFORE COMMERCIAL LAUNCH
- Complete and verify the publisher identity and contact details in the legal pages.
- Tailor privacy and cookie notices to the real form, email, hosting, analytics and payment processing configuration.
- Verify each bookmaker against the UK Gambling Commission public register and operator terms; do not invent ratings, current offers or affiliate relationships.
- Confirm permission/licensing for commercial reuse of third-party sports data.
- Complete a live test of membership submissions and Stripe payment links.
- Obtain appropriate review of gambling advertising, affiliate disclosures and applicable UK legal obligations.

CONTACT
Public contact email currently configured: betvault2026@protonmail.com
