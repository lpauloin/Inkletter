from inkletter.md_to_mjml import parse_markdown_to_mjml, wrap_mjml_body


def test_md_generation_full_syntax(ast):
    markdown_input = """\
# 📣 **New Product Launch Campaign** — *Spring 2025*

Welcome to our official campaign brief for the **MegaWidget 5000**.  
Let's make this launch unforgettable!

---

## 🚀 Campaign Goals

- **Raise awareness** about MegaWidget 5000.
- **Drive pre-orders** during the launch month.
- **Engage influencers and reviewers**.

---

## 📅 Timeline

| Phase          | Start Date | End Date   |
|----------------|------------|------------|
| Planning       | 2025-04-01 | 2025-04-15 |
| Teaser Phase   | 2025-04-16 | 2025-04-30 |
| Launch Phase   | 2025-05-01 | 2025-05-31 |
| Follow-up      | 2025-06-01 | 2025-06-15 |

---

## 📌 Key Actions

### Pre-Launch

- [x] Define target audience
- [x] Finalize product specs
- [ ] Build landing page
- [ ] Send teaser emails

### Launch Week

- [ ] Go live on website
- [ ] Announce on **social media**
- [ ] Release press release
- [ ] Partner with influencers

### Post-Launch

- [ ] Gather reviews
- [ ] Run retargeting ads
- [ ] Send thank-you emails

---

## 💬 Messaging Examples

> "**Revolutionize your workflow** — Meet the MegaWidget 5000."
>
> _"Faster, smarter, better. The tool you didn't know you needed."_

---

## 📧 Email Snippet

```html
<!DOCTYPE html>
<html>
  <body>
    <h1>Introducing the MegaWidget 5000 🚀</h1>
    <p>Pre-order now and get 20% off + free shipping!</p>
  </body>
</html>
```
"""

    expected = """\
<mjml>
  <mj-head>
    <mj-attributes>
      <mj-section padding="16px 0" background-color="#ffffff"/>
      <mj-text font-family="Helvetica, Arial, sans-serif" font-size="14px" line-height="1.6" color="#374151"/>
      <mj-table color="#374151" font-family="Helvetica, Arial, sans-serif" font-size="14px" line-height="1.6"/>
      <mj-button background-color="#1d4ed8" color="#ffffff" border-radius="6px" font-weight="700" inner-padding="12px 24px" align="center" font-family="Helvetica, Arial, sans-serif" font-size="14px"/>
      <mj-image fluid-on-mobile="true" align="center"/>
    </mj-attributes>
    <mj-style inline="inline">
      h1, h2, h3, h4, h5, h6 { font-family: Helvetica, Arial, sans-serif; color: #374151; font-weight: 700; line-height: 1.3; margin: 0; }
      h1 { font-size: 28px; }
      h2 { font-size: 22px; }
      h3 { font-size: 18px; }
      a { color: #1d4ed8; text-decoration: underline; }
      p { margin: 0 0 12px; }
      p:last-child { margin-bottom: 0; }
      blockquote { color: #6b7280; font-style: italic; border-left: 3px solid #e5e7eb; margin: 0; padding: 2px 0 2px 14px; }
      code { font-family: Menlo, Consolas, monospace; background-color: #f9fafb; color: #111827; padding: 2px 4px; border-radius: 3px; }
      pre { font-family: Menlo, Consolas, monospace; background-color: #f9fafb; color: #111827; margin: 0; padding: 12px; border-radius: 6px; overflow-x: auto; }
      ul, ol { margin: 0; padding-left: 24px; }
    </mj-style>
  </mj-head>
  <mj-body width="600px" background-color="#f9fafb">
    <mj-section>
      <mj-column>
        <mj-text>
          <h1>📣 <strong>New Product Launch Campaign</strong> — <em>Spring 2025</em></h1>
        </mj-text>
        <mj-text>
          Welcome to our official campaign brief for the <strong>MegaWidget 5000</strong>.<br/>
          Let's make this launch unforgettable!
        </mj-text>
        <mj-divider border-color="#e5e7eb" border-width="1px"/>
        <mj-text>
          <h2>🚀 Campaign Goals</h2>
        </mj-text>
        <mj-text>
          <ul>
            <li>
              <strong>Raise awareness</strong> about MegaWidget 5000.
            </li>
            <li>
              <strong>Drive pre-orders</strong> during the launch month.
            </li>
            <li>
              <strong>Engage influencers and reviewers</strong>.
            </li>
          </ul>
        </mj-text>
        <mj-divider border-color="#e5e7eb" border-width="1px"/>
        <mj-text>
          <h2>📅 Timeline</h2>
        </mj-text>
        <mj-table>
          <tr>
            <th style="border-bottom: 2px solid #e5e7eb; padding: 8px 12px; text-align: left;">Phase</th>
            <th style="border-bottom: 2px solid #e5e7eb; padding: 8px 12px; text-align: left;">Start Date</th>
            <th style="border-bottom: 2px solid #e5e7eb; padding: 8px 12px; text-align: left;">End Date</th>
          </tr>
          <tr>
            <td style="border-bottom: 1px solid #e5e7eb; padding: 8px 12px;">Planning</td>
            <td style="border-bottom: 1px solid #e5e7eb; padding: 8px 12px;">2025-04-01</td>
            <td style="border-bottom: 1px solid #e5e7eb; padding: 8px 12px;">2025-04-15</td>
          </tr>
          <tr>
            <td style="border-bottom: 1px solid #e5e7eb; padding: 8px 12px;">Teaser Phase</td>
            <td style="border-bottom: 1px solid #e5e7eb; padding: 8px 12px;">2025-04-16</td>
            <td style="border-bottom: 1px solid #e5e7eb; padding: 8px 12px;">2025-04-30</td>
          </tr>
          <tr>
            <td style="border-bottom: 1px solid #e5e7eb; padding: 8px 12px;">Launch Phase</td>
            <td style="border-bottom: 1px solid #e5e7eb; padding: 8px 12px;">2025-05-01</td>
            <td style="border-bottom: 1px solid #e5e7eb; padding: 8px 12px;">2025-05-31</td>
          </tr>
          <tr>
            <td style="border-bottom: 1px solid #e5e7eb; padding: 8px 12px;">Follow-up</td>
            <td style="border-bottom: 1px solid #e5e7eb; padding: 8px 12px;">2025-06-01</td>
            <td style="border-bottom: 1px solid #e5e7eb; padding: 8px 12px;">2025-06-15</td>
          </tr>
        </mj-table>
        <mj-divider border-color="#e5e7eb" border-width="1px"/>
        <mj-text>
          <h2>📌 Key Actions</h2>
        </mj-text>
        <mj-text>
          <h3>Pre-Launch</h3>
        </mj-text>
        <mj-text>
          <ul>
            <li style="list-style-type: none;">
              ☑ Define target audience
            </li>
            <li style="list-style-type: none;">
              ☑ Finalize product specs
            </li>
            <li style="list-style-type: none;">
              ☐ Build landing page
            </li>
            <li style="list-style-type: none;">
              ☐ Send teaser emails
            </li>
          </ul>
        </mj-text>
        <mj-text>
          <h3>Launch Week</h3>
        </mj-text>
        <mj-text>
          <ul>
            <li style="list-style-type: none;">
              ☐ Go live on website
            </li>
            <li style="list-style-type: none;">
              ☐ Announce on <strong>social media</strong>
            </li>
            <li style="list-style-type: none;">
              ☐ Release press release
            </li>
            <li style="list-style-type: none;">
              ☐ Partner with influencers
            </li>
          </ul>
        </mj-text>
        <mj-text>
          <h3>Post-Launch</h3>
        </mj-text>
        <mj-text>
          <ul>
            <li style="list-style-type: none;">
              ☐ Gather reviews
            </li>
            <li style="list-style-type: none;">
              ☐ Run retargeting ads
            </li>
            <li style="list-style-type: none;">
              ☐ Send thank-you emails
            </li>
          </ul>
        </mj-text>
        <mj-divider border-color="#e5e7eb" border-width="1px"/>
        <mj-text>
          <h2>💬 Messaging Examples</h2>
        </mj-text>
        <mj-text>
          <blockquote>
            <p>"<strong>Revolutionize your workflow</strong> — Meet the MegaWidget 5000."</p><p><em>"Faster, smarter, better. The tool you didn't know you needed."</em></p>
          </blockquote>
        </mj-text>
        <mj-divider border-color="#e5e7eb" border-width="1px"/>
        <mj-text>
          <h2>📧 Email Snippet</h2>
        </mj-text>
        <mj-text>
          <pre>
&lt;!DOCTYPE html&gt;
&lt;html&gt;
  &lt;body&gt;
    &lt;h1&gt;Introducing the MegaWidget 5000 🚀&lt;/h1&gt;
    &lt;p&gt;Pre-order now and get 20% off + free shipping!&lt;/p&gt;
  &lt;/body&gt;
&lt;/html&gt;
          </pre>
        </mj-text>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>"""

    actual = parse_markdown_to_mjml(markdown_input)
    print("actual:")
    print(actual)
    print("expected:")
    print(expected)
    assert actual == expected
