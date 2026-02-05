// Brief-Template nach DIN 5008 Form B
// Mit Falzmarken und Lochmarke
// =====================================

#let data = json("_data.json")

// Brieftyp: "business" oder "private"
#let is_business = data.letter_type == "business"

// Hilfsfunktionen
#let format_address(contact) = {
  let lines = ()
  if contact.company_name != none {
    lines.push(contact.company_name)
  }
  if contact.first_name != none or contact.last_name != none {
    let name = ""
    if contact.salutation != none { name += contact.salutation + " " }
    if contact.first_name != none { name += contact.first_name + " " }
    if contact.last_name != none { name += contact.last_name }
    lines.push(name.trim())
  }
  if contact.street != none { lines.push(contact.street) }
  if contact.zip_code != none or contact.city != none {
    let combined = ""
    if contact.zip_code != none { combined += contact.zip_code + " " }
    if contact.city != none { combined += contact.city }
    lines.push(combined.trim())
  }
  lines.join("\n")
}

#let greeting(contact) = {
  if contact.gender == "m" {
    [Sehr geehrter Herr #contact.last_name,]
  } else if contact.gender == "f" {
    [Sehr geehrte Frau #contact.last_name,]
  } else {
    [Sehr geehrte Damen und Herren,]
  }
}

// Seiteneinrichtung DIN 5008 Form B
#set page(
  paper: "a4",
  margin: (
    top: 27mm,
    bottom: 25mm,
    left: 25mm,
    right: 20mm,
  ),
  
  // Falzmarken und Lochmarke im Hintergrund
  background: {
    // Obere Falzmarke: 105mm vom oberen Rand
    place(
      top + left,
      dx: 0mm,
      dy: 115mm,
      line(length: 5mm, stroke: 0.25pt + black)
    )
    
    // Lochmarke: 148.5mm vom oberen Rand (Mitte)
    place(
      top + left,
      dx: 0mm,
      dy: 148.5mm,
      line(length: 3mm, stroke: 0.25pt + black)
    )
    
    // Untere Falzmarke: 210mm vom oberen Rand
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
    
    if is_business {
      grid(
        columns: (1fr, 1fr, 1fr),
        align: (left, center, right),
        [
          #data.sender.name
        ],
        [
          #if data.sender.contact.phone != "" [
            Tel: #data.sender.contact.phone
          ]
        ],
        [
          #if data.sender.contact.email != "" [
            #data.sender.contact.email
          ]
        ]
      )
    } else {
      align(center)[
        #data.sender.name
        #if data.sender.contact.phone != "" [ · Tel: #data.sender.contact.phone]
        #if data.sender.contact.email != "" [ · #data.sender.contact.email]
      ]
    }
  }
)

#set text(font: "Inter", size: 11pt, lang: "de")
#set par(justify: true, leading: 0.65em)

// === KOPFBEREICH ===

#if is_business {
  align(right)[
    #text(size: 14pt, weight: "bold")[#data.sender.name]
    #v(1mm)
    #text(size: 10pt)[
      #data.sender.address.street \
      #data.sender.address.zip #data.sender.address.city
      #v(1mm)
      #if data.sender.contact.phone != "" [Tel: #data.sender.contact.phone \ ]
      #if data.sender.contact.email != "" [#data.sender.contact.email]
      #if data.sender.contact.website != "" [ \ #data.sender.contact.website]
    ]
  ]
} else {
  align(right)[
    #text(size: 12pt, weight: "bold")[#data.sender.name]
    #v(1mm)
    #text(size: 10pt)[
      #data.sender.address.street \
      #data.sender.address.zip #data.sender.address.city
      #v(1mm)
      #if data.sender.contact.phone != "" [Tel: #data.sender.contact.phone \ ]
      #if data.sender.contact.email != "" [#data.sender.contact.email]
    ]
  ]
}

#v(5mm)

// === ANSCHRIFTENFELD ===
// Position: 45mm vom oberen Rand (Form B), Höhe: 45mm

#box(
  width: 85mm,
  height: 45mm,
  {
    // Rücksendeangabe
    set text(size: 8pt)
    underline[#data.sender.name · #data.sender.address.zip #data.sender.address.city]
    v(3mm)
    
    // Empfängeradresse
    set text(size: 11pt)
    format_address(data.contact)
  }
)

// === DATUM UND ZEICHEN ===

#place(
  top + right,
  dy: -40mm,
  [
    #align(right)[
      #data.doc_date
      #v(3mm)
      #if is_business and data.doc_number != "" [
        #text(size: 9pt)[Unser Zeichen: #data.doc_number]
      ]
    ]
  ]
)

#v(10mm)

// === BETREFF ===

#text(weight: "bold", size: 11pt)[#data.subject]

#v(8mm)

// === ANREDE ===

#greeting(data.contact)

#v(4mm)

// === INHALT ===

#data.content

#v(10mm)

// === GRUSSFORMEL UND UNTERSCHRIFT ===

Mit freundlichen Grüßen

#v(15mm)

#data.sender.name
