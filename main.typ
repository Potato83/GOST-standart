// Typst 0.13 или новее. Шаблон не требует сторонних пакетов.
// false — поля и абзац по ГОСТ; true — параметры приложенного DOCX.
#let department-style = false
// false позволяет размещать разделы подряд в коротком отчёте.
#let new-section-page = true

// Для сдачи нужен установленный Times New Roman.
// Для предварительного просмотра можно указать "Liberation Serif".
#let report-font = "Times New Roman"
#let indent = if department-style { 10mm } else { 12.5mm }

// --------------------- ЗАПОЛНИТЕ ЭТИ ПОЛЯ ---------------------
// Наименование организации воспроизведено из предоставленного образца.
#let university = [«САНКТ-ПЕТЕРБУРГСКИЙ НАЦИОНАЛЬНЫЙ ИССЛЕДОВАТЕЛЬСКИЙ
УНИВЕРСИТЕТ ИНФОРМАЦИОННЫХ ТЕХНОЛОГИЙ, МЕХАНИКИ И ОПТИКИ»]
#let faculty = [Факультет безопасности информационных технологий]
#let discipline = [Название дисциплины]
#let lab-number = [1]
#let lab-title = [Название лабораторной работы]
#let group = [Номер группы]
#let student = [Фамилия Имя Отчество]
#let teacher = [Фамилия Имя Отчество]
#let city = [Санкт-Петербург]
#let report-year = [2026]

#set document(title: "Отчёт по лабораторной работе", author: "Студент")
#set page(
  paper: "a4",
  margin: (left: 30mm, right: if department-style { 10mm } else { 15mm },
    top: 20mm, bottom: 20mm),
  numbering: "1",
  number-align: center + bottom,
  footer: context {
    if counter(page).get().first() > 1 {
      align(center, counter(page).display("1"))
    }
  },
)
// Явные метрики: высота строки 1em + зазор 0.5em = шаг 21pt при 14pt.
#set text(font: report-font, size: 14pt, lang: "ru", fill: black,
  top-edge: 0.8em, bottom-edge: -0.2em)
#set par(justify: true, first-line-indent: (amount: indent, all: true),
  leading: 0.5em, spacing: 0.5em)
#set heading(numbering: "1.1")
#show heading: it => {
  set text(size: 14pt, weight: "bold", hyphenate: false)
  set par(first-line-indent: 0pt, justify: false)
  block(above: 21pt, below: 21pt, sticky: true)[
    #h(indent)#if it.numbering != none {
      counter(heading).display(it.numbering)
      h(0.5em)
    }#it.body
  ]
}
#set figure(gap: 7pt)
#set figure.caption(separator: [ — ])
#show figure: set par(first-line-indent: 0pt, justify: false)
#show figure.caption: set text(hyphenate: false)
#show figure.where(kind: table): set figure.caption(
  position: top, separator: if department-style { [. ] } else { [ — ] })
#show figure.where(kind: table): set align(left)
#set math.equation(numbering: "(1)")
#set enum(numbering: "1)")
#set list(marker: [—])

#let lab-section(title) = {
  if new-section-page { pagebreak(weak: true) }
  heading(level: 1, title)
}
#let structural-section(title) = {
  pagebreak(weak: true)
  block(width: 100%, above: 0pt, below: 21pt, sticky: true)[
    #set par(first-line-indent: 0pt, justify: false)
    #align(center, text(weight: "bold", title))
  ]
}

// Титульная страница; номер страницы скрыт, но учитывается в нумерации.
#[
  #set par(first-line-indent: 0pt, justify: false, leading: 0.15em, spacing: 0.15em)
  #align(center)[
    ФЕДЕРАЛЬНОЕ ГОСУДАРСТВЕННОЕ АВТОНОМНОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ ВЫСШЕГО ОБРАЗОВАНИЯ

    #university

    #v(10mm)
    #faculty
  ]
  #v(1fr)
  #align(center)[
    Дисциплина:

    «#discipline»

    #v(12mm)
    #strong[ОТЧЕТ ПО ЛАБОРАТОРНОЙ РАБОТЕ № #lab-number]

    #lab-title
  ]
  #v(1fr)
  #align(right, block(width: 55%)[
    #set align(right)
    Выполнил:

    Студент гр. #group

    #student

    Подпись: #box(line(length: 35mm))

    #v(8mm)
    Проверил:

    #teacher

    Подпись: #box(line(length: 35mm))

    Отметка: #box(line(length: 35mm))
  ])
  #v(1fr)
  #align(center)[#city \ #report-year г.]
]
#pagebreak()

// Если требуется содержание, раскомментируйте:
// #outline(title: [СОДЕРЖАНИЕ], indent: auto)
// #pagebreak()

#lab-section[Цель работы]
Сформулируйте цель работы: какой метод нужно изучить, какую зависимость
исследовать или какой практический навык получить.

Укажите исходные данные, номер варианта и поставленные задачи.

#lab-section[Ход работы]
== Оборудование и исходные данные
Перечислите оборудование, программное обеспечение с версиями и параметры
эксперимента, необходимые для повторения работы.

== Выполнение и результаты
Опишите выполненные действия и полученные результаты. Пример оформления
показан в таблице #ref(<tab-results>, supplement: none). Замените
демонстрационные значения собственными данными.

#figure(
  table(
    columns: (25mm, 1fr, 1fr),
    align: center + horizon,
    stroke: 0.5pt,
    inset: 6pt,
    table.header([Номер опыта], [Напряжение $U$, В], [Сила тока $I$, А]),
    [1], [2,0], [0,10],
    [2], [4,0], [0,20],
  ),
  kind: table, supplement: [Таблица],
  caption: [Результаты измерений],
) <tab-results>
#v(21pt, weak: false)

Расчёт сопротивления выполняется по формуле (#ref(<eq-resistance>, supplement: none)):
$ R = U / I $ <eq-resistance>
#par(first-line-indent: 0pt)[где $R$ — сопротивление, Ом; $U$ — напряжение, В;
$I$ — сила тока, А.]

Пример размещения иллюстрации показан на рисунке #ref(<fig-example>, supplement: none).
#figure(
  // Замените rect(...) на image("image.png", width: 80%).
  rect(width: 80%, height: 25mm, stroke: 0.5pt)[
    #align(center + horizon)[Место для рисунка]
  ],
  supplement: [Рисунок],
  caption: [Название иллюстрации],
) <fig-example>

#structural-section[ЗАКЛЮЧЕНИЕ]
Сформулируйте выводы по результатам работы. Укажите, достигнута ли цель,
какие значения и зависимости получены, чем объясняются отклонения
и какие ограничения есть у использованного метода.

// Если использованы внешние материалы, добавьте список и ссылки [1] в тексте:
// #structural-section[СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ]
// #enum(numbering: "1.",
//   [Автор. Название. — Город: Издательство, год. — Число страниц.],
//   [Название ресурса. — URL: https://example.org (дата обращения: ДД.ММ.ГГГГ).],
// )

// Приложение при необходимости:
// #structural-section[ПРИЛОЖЕНИЕ А]
// #align(center)[Дополнительные материалы]
// Здесь размещаются исходные данные, листинги или большие таблицы.
