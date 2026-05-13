from __future__ import annotations

import os
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    Flowable,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


OUT_DIR = os.path.join("output", "pdf")
OUT_FILE = os.path.join(OUT_DIR, "organisation-hub-research.pdf")

PAGE_W, PAGE_H = A4


PALETTE = {
    "ink": colors.HexColor("#17202A"),
    "muted": colors.HexColor("#5F6B7A"),
    "paper": colors.HexColor("#FFFDF8"),
    "cream": colors.HexColor("#F6EFE3"),
    "peach": colors.HexColor("#F2A365"),
    "coral": colors.HexColor("#E85D75"),
    "teal": colors.HexColor("#2A9D8F"),
    "blue": colors.HexColor("#315C87"),
    "green": colors.HexColor("#477A5A"),
    "sand": colors.HexColor("#E9DCC9"),
    "yellow": colors.HexColor("#F6D365"),
    "line": colors.HexColor("#D9CBBB"),
}


def make_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "MagazineTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=34,
            leading=37,
            textColor=PALETTE["ink"],
            spaceAfter=10,
        ),
        "kicker": ParagraphStyle(
            "Kicker",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=PALETTE["coral"],
            uppercase=True,
            spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=14,
            leading=20,
            textColor=PALETTE["muted"],
            spaceAfter=16,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=PALETTE["ink"],
            spaceBefore=14,
            spaceAfter=9,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            textColor=PALETTE["blue"],
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=PALETTE["ink"],
            spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.3,
            leading=9.2,
            textColor=PALETTE["muted"],
        ),
        "boldsmall": ParagraphStyle(
            "BoldSmall",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=7.8,
            leading=9.8,
            textColor=PALETTE["ink"],
        ),
        "pull": ParagraphStyle(
            "PullQuote",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=20,
            textColor=PALETTE["ink"],
            alignment=TA_CENTER,
        ),
        "section": ParagraphStyle(
            "SectionLabel",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.white,
        ),
        "card_title": ParagraphStyle(
            "CardTitle",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=PALETTE["ink"],
        ),
        "card_body": ParagraphStyle(
            "CardBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.7,
            leading=12,
            textColor=PALETTE["ink"],
        ),
    }


styles = make_styles()


class Ribbon(Flowable):
    def __init__(self, text: str, color=PALETTE["blue"], width=170 * mm):
        super().__init__()
        self.text = text
        self.color = color
        self.width = width
        self.height = 9 * mm

    def draw(self):
        c = self.canv
        c.setFillColor(self.color)
        c.roundRect(0, 0, self.width, self.height, 3 * mm, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(5 * mm, 3 * mm, self.text.upper())


class ScoreBar(Flowable):
    def __init__(self, label: str, score: float, color=PALETTE["teal"], width=95 * mm):
        super().__init__()
        self.label = label
        self.score = score
        self.color = color
        self.width = width
        self.height = 8 * mm

    def draw(self):
        c = self.canv
        c.setFont("Helvetica-Bold", 7.4)
        c.setFillColor(PALETTE["ink"])
        c.drawString(0, 2.2 * mm, self.label)
        x = 42 * mm
        bw = self.width - x
        c.setFillColor(colors.HexColor("#EFE5D8"))
        c.roundRect(x, 1.8 * mm, bw, 3 * mm, 1.5 * mm, stroke=0, fill=1)
        c.setFillColor(self.color)
        c.roundRect(x, 1.8 * mm, bw * min(self.score, 10) / 10, 3 * mm, 1.5 * mm, stroke=0, fill=1)
        c.setFillColor(PALETTE["muted"])
        c.setFont("Helvetica", 7)
        c.drawRightString(self.width, 2.1 * mm, f"{self.score:.1f}")


class ProductCard(Flowable):
    def __init__(self, name, tagline, verdict, color, scores):
        super().__init__()
        self.name = name
        self.tagline = tagline
        self.verdict = verdict
        self.color = color
        self.scores = scores
        self.width = 170 * mm
        self.height = 48 * mm

    def draw(self):
        c = self.canv
        c.setFillColor(colors.white)
        c.roundRect(0, 0, self.width, self.height, 5 * mm, stroke=0, fill=1)
        c.setStrokeColor(PALETTE["line"])
        c.roundRect(0, 0, self.width, self.height, 5 * mm, stroke=1, fill=0)
        c.setFillColor(self.color)
        c.roundRect(0, self.height - 10 * mm, self.width, 10 * mm, 5 * mm, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(6 * mm, self.height - 6.7 * mm, self.name)
        c.setFillColor(PALETTE["ink"])
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(6 * mm, self.height - 16 * mm, self.tagline)
        c.setFont("Helvetica", 8)
        text = c.beginText(6 * mm, self.height - 22 * mm)
        text.setLeading(10)
        for line in wrap(self.verdict, 78)[:3]:
            text.textLine(line)
        c.drawText(text)
        x = 108 * mm
        y = self.height - 18 * mm
        for label, score in self.scores:
            c.setFillColor(PALETTE["muted"])
            c.setFont("Helvetica", 6.6)
            c.drawString(x, y, label)
            c.setFillColor(colors.HexColor("#EFE5D8"))
            c.roundRect(x, y - 4.4 * mm, 48 * mm, 2.4 * mm, 1.2 * mm, stroke=0, fill=1)
            c.setFillColor(self.color)
            c.roundRect(x, y - 4.4 * mm, 48 * mm * score / 10, 2.4 * mm, 1.2 * mm, stroke=0, fill=1)
            c.setFillColor(PALETTE["ink"])
            c.setFont("Helvetica-Bold", 6.6)
            c.drawRightString(x + 54 * mm, y - 3.8 * mm, f"{score:g}")
            y -= 8 * mm


def wrap(text, max_chars):
    words = text.split()
    lines = []
    current = []
    count = 0
    for word in words:
        add = len(word) + (1 if current else 0)
        if count + add > max_chars:
            lines.append(" ".join(current))
            current = [word]
            count = len(word)
        else:
            current.append(word)
            count += add
    if current:
        lines.append(" ".join(current))
    return lines


def P(text, style="body"):
    return Paragraph(text, styles[style])


def bullets(items):
    out = []
    for item in items:
        out.append(P(f"<b>-</b> {item}"))
    return out


def make_table(data, widths=None, header=True, font_size=7.5):
    if widths is None:
        widths = [50 * mm, 120 * mm]
    header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["boldsmall"],
        fontSize=font_size,
        leading=font_size + 2,
        textColor=colors.white,
    )
    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["small"],
        fontSize=font_size,
        leading=font_size + 2.4,
        textColor=PALETTE["ink"],
    )
    parsed = []
    for row_i, row in enumerate(data):
        parsed_row = []
        for cell in row:
            if isinstance(cell, str):
                parsed_row.append(Paragraph(cell, header_style if header and row_i == 0 else cell_style))
            else:
                parsed_row.append(cell)
        parsed.append(parsed_row)
    table = Table(parsed, colWidths=widths, hAlign="LEFT")
    commands = [
        ("FONT", (0, 0), (-1, -1), "Helvetica", font_size),
        ("TEXTCOLOR", (0, 0), (-1, -1), PALETTE["ink"]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.35, colors.HexColor("#E4D7C8")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    if header:
        commands += [
            ("BACKGROUND", (0, 0), (-1, 0), PALETTE["blue"]),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", font_size),
        ]
    table.setStyle(TableStyle(commands))
    return table


def product_section(name, kicker, color, verdict, best_for, watch_out, setup, sources):
    return [
        Ribbon(name, color),
        Spacer(1, 5 * mm),
        P(kicker, "h1"),
        P(f"<b>Verdict.</b> {verdict}"),
        P("<b>Best for.</b> " + best_for),
        P("<b>Watch out.</b> " + watch_out),
        P("<b>Setup sketch.</b> " + setup),
        P("<b>Useful sources.</b> " + sources, "small"),
        Spacer(1, 4 * mm),
    ]


def draw_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(PALETTE["paper"])
    canvas.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)
    canvas.setFillColor(PALETTE["cream"])
    canvas.circle(PAGE_W - 24 * mm, PAGE_H - 18 * mm, 36 * mm, stroke=0, fill=1)
    canvas.setFillColor(colors.HexColor("#F9E3D4"))
    canvas.circle(18 * mm, 26 * mm, 24 * mm, stroke=0, fill=1)
    canvas.setFillColor(PALETTE["muted"])
    canvas.setFont("Helvetica", 7)
    canvas.drawString(18 * mm, 10 * mm, "Organisation Hub Research")
    canvas.drawRightString(PAGE_W - 18 * mm, 10 * mm, f"{doc.page}")
    canvas.restoreState()


def build_story():
    story = []
    story.append(Spacer(1, 16 * mm))
    story.append(P("MAY 2026 RESEARCH REPORT", "kicker"))
    story.append(P("The Distraction Firewall", "title"))
    story.append(P("A light-mode buyer's guide to finding or building one central organisation hub for email, Todoist, calendars and Slack - with the inbox noise filtered before it reaches your brain.", "subtitle"))
    story.append(Spacer(1, 6 * mm))
    story.append(Ribbon("The refined brief", PALETTE["coral"]))
    story.append(Spacer(1, 4 * mm))
    story.append(P("You do not want another place to check. You want one calm hub you go to first, where Todoist is visible, important email is surfaced intelligently, noise is moved away, and non-critical folders are summarized later. The source systems should become plumbing, not destinations."))
    story.append(P("This reframes the evaluation. A planner with email integrations is not enough. The winning solution must act as a <b>distraction firewall</b>: classify incoming mail, protect the main view, create or update tasks, and produce scheduled digests every 3-4 hours."))
    story.append(Spacer(1, 8 * mm))
    story.append(P("The short answer", "h1"))
    story.append(make_table([
        ["Rank", "Recommendation"],
        ["1", "If you want to buy: trial <b>Superhuman Business</b> first. It supports Gmail and Outlook, has Split Inbox, built-in AI Auto Labels, custom AI labels, and Auto Archive. It is the closest off-the-shelf email command centre for the refined brief."],
        ["2", "If you want the highest-confidence firewall: use <b>SaneBox</b> underneath whichever email client wins. It filters server-side, trains by moving emails, supports custom folders/domain filters, and can send digests every 1-4 hours."],
        ["3", "If you want the exact system in your head: build a <b>Zapier Personal Ops Hub</b>. Gmail/Outlook/Slack/Todoist feed Tables, AI classifies, Interfaces shows the dashboard, Slack alerts only for genuinely important items."],
        ["4", "Use Sunsama, Akiflow or Motion only as the <b>day cockpit</b>. They are not the email brain. Pair them with Superhuman/SaneBox/Zapier rather than expecting them to decide which shopping/wine/watch/car mail is worth seeing."],
        ["Excluded", "<b>Fyxer</b> is not in the serious shortlist because you have tried it and it did not click. That matters more than any spec sheet."]
    ], widths=[22 * mm, 148 * mm], font_size=7.8))
    story.append(PageBreak())

    story.append(Ribbon("Decision matrix", PALETTE["blue"]))
    story.append(Spacer(1, 5 * mm))
    story.append(P("Who Keeps You Out Of The Inbox?", "h1"))
    story.append(P("The scores below weight your actual requirement: central hub, intelligent filtering, rule-building, Todoist visibility, Slack alerts, and minimal need to open source systems."))
    story.append(ProductCard("Superhuman Business", "Best off-the-shelf email brain", "Gmail and Outlook support, Split Inbox, built-in and custom AI Auto Labels, and Auto Archive make it the strongest buy-first candidate.", PALETTE["coral"], [("Email intelligence", 9), ("Hub potential", 7), ("Rule control", 8.5)]))
    story.append(Spacer(1, 4 * mm))
    story.append(ProductCard("Zapier Personal Ops", "Best exact-fit build", "Build the central dashboard you described: AI classified email, Todoist as truth, Slack as alert rail, 3-hour digests, and folder summaries.", PALETTE["teal"], [("Exact fit", 9.5), ("Setup effort", 5.5), ("Control", 9)]))
    story.append(Spacer(1, 4 * mm))
    story.append(ProductCard("SaneBox", "Best invisible email firewall", "Works under existing mailboxes, filters noise away, trains by moving messages, and sends digest summaries as often as every 1-4 hours.", PALETTE["green"], [("Filtering", 9), ("Central UI", 4), ("Low risk", 8.5)]))
    story.append(Spacer(1, 4 * mm))
    story.append(ProductCard("Shortwave", "Best AI Gmail-native inbox", "Beautiful AI filters, bundles, splits and todos, but Microsoft 365/Exchange is not supported and Hotmail is forwarding-only.", PALETTE["blue"], [("AI filters", 9), ("Gmail fit", 9), ("Outlook fit", 3)]))
    story.append(Spacer(1, 4 * mm))
    story.append(ProductCard("Lindy", "Best agent/chief-of-staff layer", "Good for scheduled inbox/calendar/follow-up checks, but less deterministic than rules and more expensive. Use when delegation beats dashboard control.", PALETTE["peach"], [("Autonomy", 8.5), ("Rule clarity", 5.5), ("Cost fit", 5)]))
    story.append(Spacer(1, 7 * mm))

    story.extend(product_section(
        "Superhuman",
        "The premium inbox that can become the front door",
        PALETTE["coral"],
        "Superhuman is now the best first trial for your refined brief. Split Inbox separates Important from Other; built-in Auto Labels move Marketing, News, Pitch and Social away; Business adds custom AI Auto Labels, Ask AI and Auto Drafts. It supports Gmail and Outlook, so it fits the mixed personal email reality better than Gmail-only tools.",
        "Someone who wants to open one beautiful inbox, see the important personal/work-ish threads first, and train the system through rules and AI labels rather than live in Gmail and Outlook separately.",
        "The Todoist story is weaker than the email story. It can be your email brain, but Todoist and Slack still need integration or habit glue. Business pricing is premium, and AI prompt labels require the Business plan.",
        "Create splits: Important, VIP, Axiomix, Finance/Admin, Calendar, Waiting, Other. Enable Auto Labels for Marketing, News, Pitch, Social, Bills/Invoices and Needs Response. Add custom AI labels such as 'personal commitment', 'family/logistics', 'contract/admin', 'shopping/noise', and Auto Archive obvious noise once trust builds.",
        "Superhuman Split Inbox, Auto Labels, AI overview and pricing: help.superhuman.com; superhuman.com/products/mail/control-your-inbox."
    ))
    story.append(P("Why this is compelling", "h2"))
    story.extend(bullets([
        "It explicitly solves the 'important vs other' problem before you start reading.",
        "Custom AI labels let you describe categories in language rather than hand-maintaining only sender rules.",
        "Auto Archive can keep low-value categories out of the main inbox, which matches your shopping/wine/watches/cars problem.",
        "It keeps you in one polished email client instead of bouncing between Gmail and Outlook."
    ]))
    story.append(P("Trial test", "h2"))
    story.append(P("After seven days, ask: can Superhuman show me only important personal and Axiomix-adjacent email, with shopping/promotions safely elsewhere, without opening Gmail or Outlook? If yes, keep going. If no, do not romanticise it."))
    story.append(PageBreak())

    story.extend(product_section(
        "Shortwave",
        "The clever AI inbox that stumbles on Microsoft",
        PALETTE["blue"],
        "Shortwave is excellent if Gmail can be the email universe. It has AI filters written as prompts, splits, bundles, delivery schedules, instant summaries, email todos, and an AI assistant that can organize the inbox. For the refined brief, its AI filter design is almost exactly right.",
        "A Gmail-first operator who wants to tell the inbox what to do in plain English and batch low-priority mail into bundles or scheduled delivery.",
        "Shortwave says Outlook.com/Hotmail/Live are forwarding-only and Microsoft 365/Exchange is not supported. That is a serious mismatch for Axiomix/M365 and any desire to avoid brittle forwarding bridges.",
        "If trialled, use only for personal Gmail first. Create AI filters for 'commercial temptation', 'finance/admin', 'needs action', 'personal humans', 'blogging/LinkedIn', and 'receipts'. Use delivery schedules for newsletters and shopping.",
        "Shortwave pricing, AI assistant, AI filters and provider support: shortwave.com/pricing; shortwave.com/docs."
    ))
    story.append(P("Why this is tempting", "h2"))
    story.extend(bullets([
        "AI filters can label, star, archive, delete and more based on custom prompts.",
        "Bundles and delivery schedules are a direct answer to distraction.",
        "Email todos make it feel more like a hub than a mail viewer.",
        "It has one of the nicest light, modern email experiences in the category."
    ]))
    story.append(P("Why it may fail for you", "h2"))
    story.append(P("The Microsoft limitation is not small. If Axiomix Microsoft 365 needs to be part of the hub, Shortwave is either a partial answer or a bridge too far."))
    story.append(PageBreak())

    story.extend(product_section(
        "SaneBox",
        "The invisible bouncer for every mailbox",
        PALETTE["green"],
        "SaneBox is not the central hub. It is the best low-risk way to clean the feed before any hub sees it. It works server-side, moves less important mail to folders such as @SaneLater/@SaneNews, learns by drag-and-drop training, supports domain/subject filters, and sends digests - including every 1-4 hours if you want reassurance.",
        "Someone drowning in mixed email who wants important messages left in the inbox and everything else summarized later, without switching to a new mail client.",
        "It is not pretty and it will not show Todoist beautifully. It is plumbing. But good plumbing is underrated, especially when the alternative is reading another watch advert at 10:17.",
        "Create custom folders: @Shopping, @Newsletters, @Receipts, @Travel, @WineWatchesCars, @Later. Train aggressively for a week. Leave person-to-person, finance/legal/health, Axiomix, calendar and family in Inbox. Set digest frequency to every 3-4 hours initially, then reduce once trust improves.",
        "SaneBox how it works, training, domain filters and digest controls: sanebox.com/help/155, /help/140, /help/121, /help/176."
    ))
    story.append(P("Where it shines", "h2"))
    story.extend(bullets([
        "It works with the mail server, so the result appears in any client.",
        "Training is wonderfully simple: move an email to the right folder and it remembers.",
        "Domain filters are ideal for shopping, wine, watches, car dealers, newsletters and retailers.",
        "Digest frequency can be increased to every 1-4 hours while you build trust."
    ]))
    story.append(P("The best pairing", "h2"))
    story.append(P("SaneBox plus Superhuman is the strongest buy-first stack: SaneBox keeps the pipes clean, Superhuman gives the polished central inbox. If you later add Sunsama or Todoist integrations, they consume a much cleaner signal."))

    story.extend(product_section(
        "Zapier Personal Ops Hub",
        "The build path: one dashboard, your exact rules",
        PALETTE["teal"],
        "Zapier is the strongest answer if you want exactly the hub you described. Gmail, Outlook, Slack and Todoist can feed Zaps; AI classifies; Tables store state; Interfaces displays the command centre; Slack receives only high-signal alerts. This is not a product you buy. It is a weekend build that can become your personal ops desk.",
        "A software engineer who is happy to co-create the system and wants rules expressed as plain-language classification prompts plus deterministic overrides.",
        "It requires architecture. If you overbuild it, you will create a new hobby instead of a calmer life. Start brutally small.",
        "Build Tables for Inbox Items, Task Watch, Digest Log, Source Rules. For each Gmail/Outlook email, classify as Critical, Action, Digest, Commercial, Archive. Only Critical/Action enter the dashboard or create Todoist tasks. Commercial folders are summarized every 3-4 hours or daily.",
        "Zapier Gmail, Outlook, Todoist, Tables, Interfaces, Agents and AI email templates: help.zapier.com; zapier.com/automation/use-case/using-ai-manage-email-communications-and-responses-effectively."
    ))
    story.append(P("Dashboard panels", "h2"))
    story.append(make_table([
        ["Panel", "What it shows"],
        ["Now", "Todoist overdue/today, urgent classified mail, next 4 hours of calendar."],
        ["Needs Decision", "Emails where AI found a concrete action or judgement call."],
        ["Personal Signal", "Human email, family/admin/finance/health, blogging/LinkedIn opportunities."],
        ["Axiomix", "Only permitted Microsoft 365 items, summarized and linked."],
        ["Digest Later", "Shopping, wine, watches, cars, newsletters, receipts and other non-urgent mail."],
        ["Rules", "A living list of classification rules you can edit in normal language."]
    ], widths=[38 * mm, 132 * mm], font_size=7.7))
    story.append(P("The magic rule", "h2"))
    story.append(P("Do not classify everything as a task. Classify as <b>show now</b>, <b>make task</b>, <b>digest later</b>, <b>archive</b>, or <b>needs rule review</b>. That keeps the hub clean instead of turning Todoist into a landfill."))
    story.append(PageBreak())

    story.extend(product_section(
        "Lindy",
        "The agent route: delegate the sweeps",
        PALETTE["peach"],
        "Lindy is strongest when you want an assistant to run scheduled checks across inbox, calendar and follow-ups. It is less attractive when you specifically want to inspect and tune deterministic rules yourself. Think of Lindy as a chief-of-staff layer, not the first answer to folder hygiene.",
        "Someone who wants to ask, 'what did I miss?' and receive a concise answer without building a dashboard.",
        "It is expensive, autonomous, and less transparent than a rules-first email firewall. If your pain is misunderstood categorisation, you may prefer Superhuman, SaneBox or Zapier.",
        "If trialled, connect only personal Gmail/Outlook first. Create four scheduled checks per day. Require it to draft, summarize and create Todoist tasks only after approval. Keep EDF and client-sensitive sources out.",
        "Lindy docs, Gmail integration, scheduling and pricing: docs.lindy.ai; lindy.ai/pricing."
    ))

    story.append(Ribbon("Planner cockpits", PALETTE["blue"]))
    story.append(Spacer(1, 5 * mm))
    story.append(P("Sunsama, Akiflow And Motion: Useful, But Not The Email Brain", "h1"))
    story.append(P("These tools are still relevant, but the role changed. They should not be asked to decide which incoming emails deserve your attention. They should receive already-filtered signal and help you plan the day."))
    story.append(make_table([
        ["Tool", "Best role in this architecture"],
        ["Sunsama", "The calmest daily cockpit. Excellent with Todoist, Gmail/Outlook-as-tasks and Slack capture. Pair with SaneBox or Superhuman upstream."],
        ["Akiflow", "The keyboard-heavy power planner. Strong Todoist/calendar/email capture, but less of an AI email firewall."],
        ["Motion", "The auto-scheduler. Useful if you want tasks placed on the calendar automatically, but email triage needs upstream rules or Zapier."]
    ], widths=[32 * mm, 138 * mm], font_size=7.8))
    story.append(P("If we choose a day cockpit later, my bias is Sunsama for your temperament: calm, inspectable, less likely to become yet another productivity slot machine. Motion is better if you want aggressive auto-scheduling. Akiflow is better if you want speed and command-palette control."))
    story.append(PageBreak())

    story.append(Ribbon("Recommended experiment", PALETTE["coral"]))
    story.append(Spacer(1, 5 * mm))
    story.append(P("A Two-Week Test That Will Actually Answer This", "h1"))
    story.append(P("Do not trial five products vaguely. Run two clean tests with pass/fail criteria."))
    story.append(P("Week 1: buy-first route", "h2"))
    story.extend(bullets([
        "Trial Superhuman Business with Gmail and Outlook/Hotmail first.",
        "Create splits and Auto Labels around your real categories: important humans, finance/admin, blogging/LinkedIn, Axiomix, shopping, wine, watches, cars, newsletters.",
        "Turn on Auto Archive only for categories you are comfortable hiding.",
        "Keep Todoist open as the task truth. If an email implies action, create/update a Todoist task.",
        "Pass condition: you can start from Superhuman and avoid Gmail/Outlook for a normal day."
    ]))
    story.append(P("Week 2: build route", "h2"))
    story.extend(bullets([
        "Build a small Zapier dashboard with Gmail/Outlook ingestion, AI classification and Todoist creation.",
        "Use only four categories at first: Show Now, Task, Digest Later, Archive.",
        "Create a 3-hour digest for Digest Later and a Slack DM only for Show Now.",
        "Pass condition: the dashboard shows fewer than 12 high-signal items per day and misses no obvious important mail."
    ]))
    story.append(P("Fallback safety net", "h2"))
    story.append(P("If both tests still leave email chaos, add SaneBox underneath. It is not glamorous, but it is purpose-built for the exact problem of moving unimportant mail away and summarizing it later."))

    story.append(Ribbon("Build spec", PALETTE["teal"]))
    story.append(Spacer(1, 5 * mm))
    story.append(P("If We Build Our Own", "h1"))
    story.append(P("The first custom version should be tiny. A website with four panels, one rules page, and one digest. No heroic architecture. No life OS cathedral."))
    story.append(make_table([
        ["Component", "Spec"],
        ["Inputs", "Gmail, Microsoft Outlook/Hotmail, Todoist, Google/Outlook Calendar, Slack saved messages or DMs."],
        ["Classifier", "LLM plus deterministic rules. Output: importance, category, action needed, confidence, reason, suggested Todoist task."],
        ["Inbox view", "Only Show Now and Task items. Digest Later is hidden by default."],
        ["Rules UI", "Plain-English categories: 'wine/watch/car/shopping promos go to Digest Later unless billing/refund/delivery problem'."],
        ["Digest", "Every 3-4 hours initially; daily once trust improves. Summarize commercial folders without pulling you into them."],
        ["Safety", "Never delete automatically at first. Archive only after a training period. Always link back to source mail."]
    ], widths=[34 * mm, 136 * mm], font_size=7.6))
    story.append(P("The engineering north star", "h2"))
    story.append(P("The system should make it emotionally easy to not check email. If it cannot confidently say 'nothing important is waiting', it has failed."))
    story.append(Spacer(1, 8 * mm))

    story.append(Ribbon("Sources", PALETTE["blue"]))
    story.append(Spacer(1, 5 * mm))
    story.append(P("Selected Sources", "h1"))
    sources = [
        "Superhuman Split Inbox: https://help.superhuman.com/hc/en-us/articles/38449611367187-Split-Inbox-Basics",
        "Superhuman Auto Labels: https://help.superhuman.com/hc/en-us/articles/40127432866323-Auto-Labels",
        "Superhuman Pricing: https://help.superhuman.com/hc/en-us/articles/38456109456147-Pricing-Plans",
        "Shortwave Pricing and AI filters: https://www.shortwave.com/pricing/",
        "Shortwave provider support: https://www.shortwave.com/docs/how-tos/microsoft-outlook-exchange-other-sign-in-support/",
        "Shortwave AI Assistant: https://www.shortwave.com/docs/guides/ai-assistant/",
        "SaneBox how it works: https://www.sanebox.com/help/155-how-does-sanebox-work",
        "SaneBox training: https://www.sanebox.com/help/140-how-do-i-train-teach-sanebox",
        "SaneBox digest frequency: https://www.sanebox.com/help/176-do-you-fear-missing-important-emails",
        "Zapier Gmail app: https://help.zapier.com/hc/en-us/articles/8495933589645-How-to-get-started-with-Gmail-on-Zapier",
        "Zapier Outlook app: https://help.zapier.com/hc/en-us/articles/18836255979277-How-to-get-started-with-Microsoft-Outlook-on-Zapier",
        "Zapier Tables: https://help.zapier.com/hc/en-us/articles/29712888250509-Zapier-Tables-quick-start-guide",
        "Zapier Interfaces: https://help.zapier.com/hc/en-us/articles/14490267815949-Create-interactive-pages-and-apps-with-Zapier-Interfaces-Beta-",
        "Sunsama integrations: https://help.sunsama.com/docs/integrations/calendar/",
        "Akiflow integrations: https://akiflow.com/integrations",
        "Motion integrations: https://www.usemotion.com/features/integrations",
        "Lindy docs: https://docs.lindy.ai/",
    ]
    for source in sources:
        story.append(P(source, "small"))
    return story


def build_pdf():
    os.makedirs(OUT_DIR, exist_ok=True)
    doc = SimpleDocTemplate(
        OUT_FILE,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title="The Distraction Firewall",
        author="Codex",
    )
    story = build_story()
    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    return OUT_FILE


if __name__ == "__main__":
    print(build_pdf())
