// Rechnungs-Template nach DIN 5008
// Mit Falzmarken, Lochmarke und Kleinunternehmer-Unterstützung
// =============================================================

#let data = json("_data.json")

// Kleinunternehmer-Flag aus Sender-Daten
#let is_kleinunternehmer = if "kleinunternehmer" in data.sender { data.sender.kleinunternehmer } else { false }

// Euro-Formatierung
#let euro(amount) = {
  let rounded = calc.round(amount, digits: 2)
  let str_amount = str(rounded)
  let parts = str_amount.split(".")
  let euros = parts.at(0)
  let cents = if parts.len() > 1 { parts.at(1) } else { "00" }
  if cents.len() == 1 { cents = cents + "0" }
  euros + "," + cents + " €"
}

// Seiteneinrichtung
#set page(
  paper: "a4",
  margin: (top: 27mm, bottom: 25mm, left: 25mm, right: 20mm),
  
  // Falzmarken und Lochmarke
  background: {
    place(
      top + left,
      dx: 0mm,
      dy: 115mm,
      line(length: 5mm, stroke: 0.25pt + black)
    )
    place(
      top + left,
      dx: 0mm,
      dy: 148.5mm,
      line(length: 3mm, stroke: 0.25pt + black)
    )
    place(
      top + left,
      dx: 0mm,
      dy: 210mm,
      line(length: 5mm, stroke: 0.25pt + black)
    )
  },
  
  footer: {
    set text(size: 8pt)
    line(length: 100%, stroke: 0.5pt)
    v(2mm)
    grid(
      columns: (1fr, 1fr, 1fr),
      [
        #data.sender.name \
        #data.sender.address.street
      ],
      [
        #if not is_kleinunternehmer and data.sender.tax.ustid != "" [
          USt-IdNr.: #data.sender.tax.ustid
        ]
        #if data.sender.tax.steuernummer != "" [
          \ Steuernr.: #data.sender.tax.steuernummer
        ]
      ],
      [
        #if data.sender.bank.iban != "" [
          IBAN: #data.sender.bank.iban \
          BIC: #data.sender.bank.bic
        ]
      ]
    )
  }
)

#set text(font: "Inter", size: 10pt, lang: "de")

// === KOPFBEREICH ===

#align(right)[
  #text(size: 12pt, weight: "bold")[#data.sender.name]
  #v(1mm)
  #text(size: 9pt)[
    #data.sender.address.street \
    #data.sender.address.zip #data.sender.address.city
  ]
]

#v(3mm)

// === ANSCHRIFTENFELD UND INFOBOX NEBENEINANDER ===

#grid(
  columns: (85mm, 1fr),
  gutter: 10mm,
  
  // Linke Spalte: Anschriftenfeld
  box(height: 45mm)[
    #set text(size: 8pt)
    #underline[#data.sender.name · #data.sender.address.zip #data.sender.address.city]
    #v(2mm)
    #set text(size: 10pt)
    #if data.contact.company_name != none [#data.contact.company_name \ ]
    #if data.contact.first_name != none or data.contact.last_name != none [
      #data.contact.first_name #data.contact.last_name \
    ]
    #if data.contact.street != none [#data.contact.street \ ]
    #data.contact.zip_code #data.contact.city
  ],
  
  // Rechte Spalte: Rechnungsdaten in Box
  align(right)[
    #box(
      stroke: 0.5pt + black,
      inset: 10pt,
      radius: 2pt,
    )[
      #set text(size: 10pt)
      #table(
        columns: (auto, auto),
        stroke: none,
        align: (left, right),
        inset: 3pt,
        [Rechnungsnummer:], [*#data.doc_number*],
        [Rechnungsdatum:], [#data.doc_date],
        [Zahlbar bis:], [#data.due_date],
      )
    ]
  ]
)

#v(8mm)

// === BETREFF ===

#text(weight: "bold", size: 11pt)[Rechnung #data.doc_number]

#v(6mm)

// === POSITIONSTABELLE ===

#table(
  columns: (auto, 1fr, auto, auto, auto, auto),
  stroke: (x, y) => if y == 0 { (bottom: 1pt) } else if y > 0 { (bottom: 0.5pt + gray) } else { none },
  align: (center, left, right, center, right, right),
  inset: 5pt,
  
  table.header(
    [*Pos*], [*Beschreibung*], [*Menge*], [*Einheit*], [*Einzelpreis*], [*Gesamt*],
  ),
  
  ..data.positions.enumerate().map(((i, pos)) => (
    str(i + 1),
    pos.description,
    str(pos.quantity),
    pos.unit,
    euro(pos.unit_price),
    euro(pos.quantity * pos.unit_price)
  )).flatten()
)

#v(4mm)

// === SUMMENBLOCK ===

#align(right)[
  #box(width: 200pt)[
    #if is_kleinunternehmer {
      // Kleinunternehmer: Keine MwSt.
      table(
        columns: (1fr, auto),
        stroke: none,
        align: (left, right),
        inset: 4pt,
        table.hline(stroke: 1pt),
        [*Rechnungsbetrag:*], [*#euro(data.net_total)*],
      )
    } else {
      // Regelbesteuerung: Mit MwSt.
      table(
        columns: (1fr, auto),
        stroke: none,
        align: (left, right),
        inset: 4pt,
        [Nettobetrag:], [#euro(data.net_total)],
        [zzgl. 19% MwSt.:], [#euro(data.vat_total)],
        table.hline(stroke: 1pt),
        [*Rechnungsbetrag:*], [*#euro(data.gross_total)*],
      )
    }
  ]
]

#v(6mm)

// === KLEINUNTERNEHMER-HINWEIS ===

#if is_kleinunternehmer [
  #text(size: 9pt, style: "italic")[Gemäß § 19 UStG wird keine Umsatzsteuer berechnet.]
  #v(4mm)
]

// === ZAHLUNGSHINWEIS ===

Bitte überweisen Sie den Betrag bis zum *#data.due_date* auf folgendes Konto:

#v(3mm)

#table(
  columns: (auto, 1fr),
  stroke: none,
  inset: 2pt,
  [Kontoinhaber:], [#data.sender.name],
  [IBAN:], [#data.sender.bank.iban],
  [BIC:], [#data.sender.bank.bic],
  [Bank:], [#data.sender.bank.bank_name],
  [Verwendungszweck:], [#data.doc_number],
)

#v(6mm)

// === NOTIZEN ===

#if data.notes != "" [
  #data.notes
  #v(4mm)
]

Vielen Dank für Ihren Auftrag!
