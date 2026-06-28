#set page(margin: 42pt)
#set text(font: "Arial", size: 10pt)
#set heading(numbering: none)

#let accent = rgb("#1457d9")
#let good = rgb("#11845b")
#let warn = rgb("#b86b00")
#let muted = rgb("#667085")
#let panel = rgb("#f6f8fb")

#let stat(label, value, color: accent) = block[
  #rect(fill: panel, radius: 5pt, inset: 10pt, width: 100%)[
    #text(size: 8pt, fill: muted, weight: "bold")[#upper(label)]
    #linebreak()
    #text(size: 18pt, fill: color, weight: "bold")[#value]
  ]
]

= Price Monitoring Alert Report

#text(fill: muted)[
  Price monitoring summary for public product pages. The report highlights
  which items are below target price and writes CSV files for automation.
]

#grid(columns: (1fr, 1fr, 1fr, 1fr), gutter: 8pt)[
  #stat("Products checked", "4")
][
  #stat("Alerts", "3", color: warn)
][
  #stat("Potential savings", "$91.51", color: good)
][
  #stat("Outputs", "CSV + PDF")
]

== Alert Queue

#table(
  columns: (1.2fr, 1.8fr, .8fr, .8fr),
  inset: 5pt,
  stroke: rgb("#d0d5dd"),
  [*Product*], [*Title*], [*Price*], [*Below Target*],
  [Demo Laptop], [Demo Laptop 14], [\$849.99], [\$50.01],
  [Ergonomic Chair], [Ergo Chair Pro], [\$189.50], [\$30.50],
  [Noise Cancelling Headset], [Office ANC Headset], [\$119.00], [\$11.00],
)

== Full Snapshot

#table(
  columns: (1.1fr, 1.8fr, .7fr, .7fr),
  inset: 5pt,
  stroke: rgb("#d0d5dd"),
  [*Product*], [*Title*], [*Price*], [*Target*],
  [Demo Laptop], [Demo Laptop 14], [\$849.99], [\$900.00],
  [USB-C Monitor], [27 inch USB-C Monitor], [\$259.00], [\$250.00],
  [Ergonomic Chair], [Ergo Chair Pro], [\$189.50], [\$220.00],
  [Noise Cancelling Headset], [Office ANC Headset], [\$119.00], [\$130.00],
)

== Delivery Notes

- Snapshot CSV: `outputs/sample_report/snapshot.csv`
- Alerts CSV: `outputs/sample_report/alerts.csv`
- Alerts trigger only when current price is at or below the configured target.
- The pipeline does not bypass logins, CAPTCHAs, account gates, or site restrictions.
