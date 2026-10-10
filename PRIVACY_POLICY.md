# Privacy Policy

**Effective date:** 2026-10-10

This Privacy Policy describes what information the Discord Join Quiz Bot ("the Bot") handles, why, and for how long.

## Who this policy applies to

The Bot is open-source software that anyone can run. This policy covers **the instance of the Bot operated for Hard Way Hacking and Coding** ("we", "us").

If you encounter a copy of the Bot run by someone else (a "self-hosted instance"), that operator controls the data it handles and is responsible for their own privacy practices. The descriptions below of what the software does still apply to an unmodified copy, but the retention, logging, and contact details may differ.

## Information the Bot handles

The Bot only operates inside Discord servers ("guilds") where a server administrator has added it. It does not have a website, does not use cookies, and does not collect information outside of Discord.

### Information received from Discord

When you join a server that uses the Bot, Discord provides the Bot with standard member information, including:

- Your Discord user ID, username, and display name
- The server (guild) ID and name
- Your roles in that server

The Bot also receives your interactions with it: the buttons you select while answering quiz questions, and slash commands used by moderators (such as `/banish` and `/requiz`).

### Information the Bot stores

To track how many times you have attempted a server's quiz, the Bot stores the following in a file on the operator's server:

| Data | Purpose |
| --- | --- |
| Server (guild) ID | Associate the attempt with the correct server |
| Discord user ID | Associate the attempt with you |
| Number of quiz attempts | Determine which consequence applies if you fail again |
| Timestamp of your last attempt | Determine when the record can be deleted |

The Bot does **not** store your quiz answers, your messages, your username, or any other content.

### Information in logs and moderation channels

- **Operational logs:** The Bot writes operational logs that include your username, user ID, and server name when it starts, completes, or cancels a quiz, or takes a moderation action involving you.
- **Server audit channel:** If a server's administrators configure a log channel, the Bot posts audit messages there containing your username, user ID, and quiz outcome (for example, passed, failed, timed out, or matched a configured name filter, and the action taken). Those messages become part of that Discord server and are controlled by its administrators and by Discord, not by us.
- **Quiz threads:** The Bot creates a private thread for your quiz and deletes it when the quiz ends.
- **Metrics:** The Bot keeps aggregate counts (for example, number of quizzes passed or failed) in memory. These are not linked to individual users and are discarded when the Bot restarts.

## How the information is used

Information is used only to run the quiz and enforce the server's configured rules: starting your quiz, assigning or removing roles, applying the configured consequences (such as a restricted role, kick, or ban) on failure, and providing an audit trail to server moderators.

We do not sell, rent, or share your information with third parties, use it for advertising, or use it to train machine learning models.

## Retention

- **Quiz-attempt records** are deleted automatically once 24 hours have passed since your last attempt (the cleanup runs about every 20 minutes).
- **Operational logs** are kept only as long as needed to operate and troubleshoot the Bot.
- **Audit messages** posted to a server's log channel remain until that server's moderators or Discord delete them.

## Your choices and rights

- You can avoid the Bot entirely by not joining servers that use it, or by leaving them.
- You may ask us about, or ask us to delete, information our instance holds about you using the contact details below. Because attempt records expire after 24 hours, there is usually nothing left to delete.
- Audit messages in a server's log channel are controlled by that server's administrators; contact them to have those removed.
- Your use of Discord itself is governed by [Discord's Privacy Policy](https://discord.com/privacy).

## Children

The Bot is intended for use within Discord, which requires users to meet its minimum age requirement. We do not knowingly collect information from anyone below that age.

## Security

Stored data is limited to the identifiers listed above and is kept on infrastructure controlled by the operator. No method of storage or transmission is completely secure, but we take reasonable steps to protect it.

## Changes to this policy

We may update this policy from time to time. Changes take effect when posted in this repository, and the effective date above will be updated. The full history of changes is available in the repository's commit history.

## Contact

For questions or requests about this policy, contact **Loredous** on Discord.

Project: [github.com/loredous/discord-join-quiz-bot](https://github.com/loredous/discord-join-quiz-bot)
