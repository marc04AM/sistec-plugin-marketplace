# src/img/ — manual images

Folder for the images/screenshots to insert into the manual.

## Naming convention
Name files descriptively and stably, so that the placeholders in the manual
do not change when the image is supplied:

```
<section>-<subject>.png
```

Examples:
- `2.2-login.png` — user login window.
- `3.1-layout-generale.png` — general panel layout.
- `3.2-menu-laterale.png` — side menu.
- `4-ricetta-pagina.png` — Recipe page.
- `5-home-taskboard.png` — HOME page with task list.
- `7.1-palletstateview.png` — unloading bay indicator.
- `8.3-diagnostica-avvio.png` — startup checks window.

## Referencing in the manual
In Markdown files the image is inserted as:

```markdown
![menu laterale](src/img/3.2-menu-laterale.png)
*Immagine: Menu laterale dell'HMI.*
```

The `alt` text (`![...]`) is rendered by `style.css` as a caption below the image.

## Image status
The list of placeholders still without an image is kept in
`immagini-richieste.md` (at the project root).
