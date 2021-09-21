![Banner](banner.jpg)

# Social Media CRON

Using [GitHub Actions](https://github.com/nnadeau/social-media-cron/actions) as a simple hosted CRON job runner for tending my social media.

## Motivation

- I like automation
- *Infrastructure as code* is a great idea
- I have too many Raspberry Pis and hobby servers to manage

## Usage

- Secrets are stored as [repository secrets](https://docs.github.com/en/actions/reference/encrypted-secrets) and access as [environment variables in the workflow](https://docs.github.com/en/actions/reference/encrypted-secrets#using-encrypted-secrets-in-a-workflow)
  - [Repository secrets settings](https://github.com/nnadeau/social-media-cron/settings/secrets/actions)
- Scripts are designed to run both locally and in Actions
- [`settings.toml`](settings.toml) stores configurable settings

### Twitter

- Get your tokens from [the developer portal](https://developer.twitter.com/en/portal/dashboard)

---

Photo by <a href="https://unsplash.com/@whitfieldjordan?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Jordan Whitfield</a> on <a href="https://unsplash.com/s/photos/efficient?utm_source=unsplash&utm_medium=referral&utm_content=creditCopyText">Unsplash</a>
