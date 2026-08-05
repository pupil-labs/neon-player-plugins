# Contributing

First off, thank you for considering contributing to Neon Player Plugins! It's people like you that make the Neon Player community such a great place.

## How to add a plugin

This repository serves **only as a directory** of plugins. We do not host plugin source code directly in this repository.

If you have developed a plugin for Neon Player and want to share it with the community, you must host it externally (in its own dedicated repository) and then submit a Pull Request to add a link to it in our `README.md`. 

### Adding your plugin to the README

To add your plugin to the list, please follow these steps:

1. Fork the repository.
2. Add a screenshot of your plugin (1280x720px in `.webp` format) to the `assets/` folder.
3. Edit the `README.md` to include your plugin in the appropriate category, using the provided template format. Not fitting any category? You can create a new one, but please make sure it is relevant.
4. Create a Pull Request with a clear title and description of your plugin.

### Plugin Template

Please use the following format when adding to the `README.md`:

```markdown
### [Plugin Name](https://github.com/yourusername/your-plugin-repo)

| Screenshot | Brief description / Comments | Author | Date/Version last tested | Link | License |
|--- |--- |--- |--- |--- |--- |
| ![plugin screenshot](./assets/your_screenshot.webp) | Brief description of what your plugin does. | @yourusername | 6.0.x (DD/MM/YY) | [Repo Link](https://github.com/yourusername/your-plugin-repo) | MIT (or Proprietary) |

**Detailed Description:**
Add a longer description here. You can explain how to use the plugin, its features, any specific requirements, or how to purchase/access it if it is proprietary.
```

Add the hyperlink on the ToC. 

## Guidelines
- Ensure your plugin works with the latest or a recent version of Neon Player.
- Keep the table description concise, and use the section below the table for longer explanations.
- If your plugin requires external dependencies, please mention them in the detailed description or provide a link to the installation instructions.
- Ensure you specify an appropriate license for your plugin in the README table (e.g., MIT, Apache 2.0). If your plugin is closed-source, simply write "Proprietary".

We look forward to your contributions!
