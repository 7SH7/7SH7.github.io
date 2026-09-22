#!/usr/bin/env python3
"""Build the single-file portfolio with Python's standard library only."""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
CONTENT_PATH = ROOT / "content.json"
TEMPLATE_PATH = ROOT / "template.html"
OUTPUT_PATH = ROOT / "index.html"
LANGUAGES = ("ko", "ja", "en")
PROJECT_CATEGORIES = {"cloud", "embedded", "backend", "ai-data"}
# MICEMore leads the live section already, so the project grid opens with the next
# strongest cloud and backend work. Every card is the same size.
FEATURED_ORDER = (
    "ugly-pick",
    "smart-factory-multi-agent",
    "ssobbi",
    "hot-spot",
    "llm-for-science",
    "vehicle-diagnostics-r300",
    "micemore",
)
ATTR_SECTION_INTRO = 'class="section-intro"'
ATTR_EYEBROW = 'class="eyebrow"'
ATTR_HERO_LEDE = 'class="hero-lede"'
ATTR_BADGE = 'class="badge"'
ATTR_STAT_LABEL = 'class="stat-label"'
ATTR_LIVE_BADGE = 'class="badge badge--live"'
ATTR_META = 'class="meta"'
ATTR_MUTED = 'class="muted"'
ATTR_TIMELINE_DATE = 'class="timeline-date"'
ATTR_GENERATED_NOTE = 'class="meta generated-note"'

COPY: dict[str, dict[str, str]] = {
    "skip_to_content": {
        "ko": "본문으로 건너뛰기",
        "ja": "本文へスキップ",
        "en": "Skip to content",
    },
    "nav_label": {"ko": "주요 메뉴", "ja": "メインメニュー", "en": "Primary navigation"},
    "language_label": {"ko": "언어 선택", "ja": "言語選択", "en": "Choose language"},
    "hero_eyebrow": {
        "ko": "INFRASTRUCTURE · CLOUD · EMBEDDED",
        "ja": "INFRASTRUCTURE · CLOUD · EMBEDDED",
        "en": "INFRASTRUCTURE · CLOUD · EMBEDDED",
    },
    "live_intro": {
        "ko": "말이 아니라 현재 동작하는 서비스와 운영 책임으로 증명.",
        "ja": "言葉ではなく、稼働中のサービスと運用責任で証明。",
        "en": "Evidence through a running service and direct operational responsibility.",
    },
    "stats_label": {"ko": "핵심 수치", "ja": "主要指標", "en": "Key metrics"},
    "experience_intro": {
        "ko": "서비스 운영, 데이터 품질, 실무 개발, 오픈소스 연구와 교육을 연결한 경력.",
        "ja": "サービス運用、データ品質、実務開発、オープンソース研究、教育をつないだ経歴。",
        "en": "Experience connecting live operations, data quality, product development, open-source research, and mentoring.",
    },
    "projects_intro": {
        "ko": "분야별 필터로 구현 범위를 확인. 역할·기여도·수치·근거 링크를 함께 표기.",
        "ja": "分野別フィルターで実装範囲を確認。役割・貢献度・数値・根拠リンクを併記。",
        "en": "Filter by discipline; every entry states role, contribution, metrics, and available evidence.",
    },
    "featured_projects": {"ko": "대표 프로젝트", "ja": "主要プロジェクト", "en": "Featured projects"},
    "screens_heading": {"ko": "서비스 화면", "ja": "サービス画面", "en": "Service screens"},
    "additional_projects": {"ko": "추가 프로젝트", "ja": "その他のプロジェクト", "en": "Additional projects"},
    "more_projects_summary": {
        "ko": "추가 프로젝트와 공개 저장소 보기",
        "ja": "その他のプロジェクトと公開リポジトリを見る",
        "en": "View additional projects and public repositories",
    },
    "more_activities_summary": {
        "ko": "활동 전체 보기",
        "ja": "活動一覧を見る",
        "en": "View the full activity list",
    },
    "repositories_intro": {
        "ko": "공개 저장소의 성격과 포크 여부를 구분해 제시. 프로젝트 역할 설명은 저장소 소유권과 별개.",
        "ja": "公開リポジトリの性格とForkの有無を明示。プロジェクトでの役割はリポジトリ所有権とは別に記載。",
        "en": "Public repositories are labeled by source or fork status; project responsibilities are stated independently of repository ownership.",
    },
    "filter_label": {"ko": "프로젝트 분야 필터", "ja": "プロジェクト分野フィルター", "en": "Project category filters"},
    "filter_status": {"ko": "프로젝트 필터 결과", "ja": "フィルター結果", "en": "Project filter results"},
    "awards_intro": {
        "ko": "주최·대상·순위를 확인할 수 있는 수상 이력만 수록.",
        "ja": "主催・対象・順位を確認できる受賞歴のみ掲載。",
        "en": "Only awards with verifiable organizer, project, and placement details are included.",
    },
    "activities_intro": {
        "ko": "클라우드·AI·임베디드 학습과 멘토링, 오픈소스 기여.",
        "ja": "クラウド・AI・組み込みの学習、メンタリング、オープンソース貢献。",
        "en": "Cloud, AI, and embedded training alongside mentoring and open-source contribution.",
    },
    "skills_intro": {
        "ko": "기술 이름보다 실제 사용 맥락을 함께 기록.",
        "ja": "技術名だけでなく、実際に使用した文脈も記載。",
        "en": "Technologies are paired with the context in which they were used.",
    },
    "education_intro": {
        "ko": "전자·컴퓨터공학 기반과 보유 자격.",
        "ja": "電子・コンピュータ工学の基礎と保有資格。",
        "en": "Electrical and computer engineering foundations and held credentials.",
    },
    "contact_intro": {
        "ko": "프로젝트와 기술 판단의 근거는 아래 공개 링크에서 확인 가능.",
        "ja": "プロジェクトと技術判断の根拠は、以下の公開リンクから確認可能。",
        "en": "Public evidence for the projects and engineering decisions is available through the links below.",
    },
    "table_period": {"ko": "기간", "ja": "期間", "en": "Period"},
    "table_award": {"ko": "수상", "ja": "受賞", "en": "Award"},
    "table_issuer": {"ko": "주최", "ja": "主催", "en": "Issuer"},
    "table_evidence": {"ko": "대상 · 근거", "ja": "対象・根拠", "en": "Project & evidence"},
    "table_activity": {"ko": "활동", "ja": "活動", "en": "Activity"},
    "table_organization": {"ko": "기관", "ja": "機関", "en": "Organization"},
    "table_details": {"ko": "내용", "ja": "内容", "en": "Details"},
    "table_category": {"ko": "분류", "ja": "分類", "en": "Category"},
    "table_stack": {"ko": "기술", "ja": "技術", "en": "Technology"},
    "table_context": {"ko": "사용 맥락", "ja": "使用文脈", "en": "Usage context"},
    "education_card": {"ko": "학력", "ja": "学歴", "en": "Education"},
    "credentials_card": {"ko": "자격 · 병역", "ja": "資格・兵役", "en": "Credentials & Service"},
    "certifications": {"ko": "자격", "ja": "資格", "en": "Certifications"},
    "languages": {"ko": "어학", "ja": "語学", "en": "Languages"},
    "pending_value": {"ko": "교체 필요", "ja": "要更新", "en": "Replace before publishing"},
    "open_repository": {"ko": "저장소 열기", "ja": "リポジトリを開く", "en": "Open repository"},
    "generated_note": {
        "ko": "content.json과 GitHub API를 바탕으로 생성",
        "ja": "content.jsonとGitHub APIから生成",
        "en": "Generated from content.json and the GitHub API",
    },
}


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def fetch_public_repo_count(fallback: int, offline: bool) -> int:
    if offline:
        return fallback

    request = urllib.request.Request(
        "https://api.github.com/users/7SH7",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "7SH7-portfolio-builder"},
    )
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    try:
        with urllib.request.urlopen(request, timeout=6) as response:
            count = json.load(response).get("public_repos")
        if isinstance(count, int) and count > 0:
            return count
    except (OSError, ValueError, urllib.error.URLError) as error:
        print(f"GitHub API unavailable; using fallback repository count ({fallback}): {error}", file=sys.stderr)
    return fallback


class Renderer:
    def __init__(self, content: dict[str, Any]) -> None:
        self.content = content
        self.translations: dict[str, dict[str, str]] = {}

    def add_translation(self, key: str, value: dict[str, str]) -> None:
        missing = set(LANGUAGES) - set(value)
        if missing:
            raise ValueError(f"Missing translations for {key}: {', '.join(sorted(missing))}")
        normalized = {language: str(value[language]) for language in LANGUAGES}
        previous = self.translations.get(key)
        if previous is not None and previous != normalized:
            raise ValueError(f"Translation key reused with different values: {key}")
        self.translations[key] = normalized

    def localized(self, tag: str, key: str, value: dict[str, str], attrs: str = "") -> str:
        self.add_translation(key, value)
        attrs = f" {attrs.strip()}" if attrs.strip() else ""
        return f'<{tag}{attrs} data-i18n="{esc(key)}">{esc(value["ko"])}</{tag}>'

    def localized_text(self, key: str, value: dict[str, str]) -> str:
        self.add_translation(key, value)
        return f'<span data-i18n="{esc(key)}">{esc(value["ko"])}</span>'

    def translated_label_attrs(self, key: str, value: dict[str, str]) -> str:
        self.add_translation(key, value)
        return f'data-label="{esc(value["ko"])}" data-i18n-label="{esc(key)}"'

    def translated_aria_attrs(self, key: str, value: dict[str, str]) -> str:
        self.add_translation(key, value)
        return f'aria-label="{esc(value["ko"])}" data-i18n-aria-label="{esc(key)}"'

    def links(self, links: list[dict[str, Any]] | None, prefix: str, primary: bool = False) -> str:
        if not links:
            return ""
        items: list[str] = []
        for index, link in enumerate(links):
            classes = "button button--primary" if primary and index == 0 else "button"
            label = self.localized_text(f"{prefix}.link.{index}", link["label"])
            items.append(f'<a class="{classes}" href="{esc(link["url"])}">{label}</a>')
        return f'<div class="actions">{"".join(items)}</div>'

    def section_heading(self, number: str, key: str, title: dict[str, str], intro_key: str) -> str:
        return (
            '<div class="section-heading">'
            '<div>'
            f'<p class="section-label">{esc(number)} // {esc(key.upper())}</p>'
            f'{self.localized("h2", f"section.{key}.title", title)}'
            '</div>'
            f'{self.localized("p", f"section.{key}.intro", COPY[intro_key], ATTR_SECTION_INTRO)}'
            '</div>'
        )

    def tags(self, items: list[str]) -> str:
        if not items:
            return ""
        return '<ul class="tag-list" aria-label="Technologies">' + "".join(
            f'<li class="tag">{esc(item)}</li>' for item in items
        ) + "</ul>"

    def category_badges(self, categories: list[str], prefix: str) -> str:
        labels = self.content["meta"]["category_labels"]
        return '<div class="tag-list">' + "".join(
            self.localized(
                "span",
                f"{prefix}.category.{category}",
                labels[category],
                'class="badge badge--signal"',
            )
            for category in categories
        ) + "</div>"

    def header(self) -> str:
        sections = self.content["meta"]["sections"]
        nav_items = (
            ("live", sections["live"]),
            ("experience", sections["experience"]),
            ("projects", sections["projects"]),
            ("awards", sections["awards"]),
            ("skills", sections["skills"]),
            ("contact", sections["contact"]),
        )
        nav = "".join(
            f'<li><a href="#{anchor}">{self.localized_text(f"nav.{anchor}", label)}</a></li>'
            for anchor, label in nav_items
        )
        nav_aria = self.translated_aria_attrs("nav.label", COPY["nav_label"])
        lang_aria = self.translated_aria_attrs("language.label", COPY["language_label"])
        return (
            '<header class="site-header">'
            '<div class="container header-inner">'
            '<a class="brand" href="#top">SEUNGHWAN.KIM</a>'
            f'<nav class="primary-nav" {nav_aria}><ul>{nav}</ul></nav>'
            f'<div class="language-switcher" {lang_aria}>'
            '<button type="button" data-lang-button="ko" aria-pressed="true">KR</button>'
            '<button type="button" data-lang-button="ja" aria-pressed="false">JP</button>'
            '<button type="button" data-lang-button="en" aria-pressed="false">EN</button>'
            '</div></div></header>'
        )

    def hero(self) -> str:
        profile = self.content["profile"]
        # Name and role lead, then the headline. The evidence that used to sit
        # in a side column repeats verbatim in the live section and the project
        # cards below it, and one of its three lines put embedded work at the
        # top of a page whose argument is cloud and backend.
        byline = {
            language: f'{profile["name"][language]} · {profile["title"][language]}'
            for language in LANGUAGES
        }
        return (
            '<section class="hero" id="top">'
            '<div class="container hero-stack">'
            f'{self.localized("p", "hero.byline", byline, ATTR_EYEBROW)}'
            f'{self.localized("h1", "hero.headline", profile["headline"])}'
            f'{self.localized("p", "hero.summary", profile["summary"], ATTR_HERO_LEDE)}'
            '<div class="tag-list">'
            f'{self.localized("span", "hero.location", profile["location"], ATTR_BADGE)}'
            f'{self.localized("span", "hero.education", profile["education_summary"], ATTR_BADGE)}'
            '</div>'
            '<div class="actions">'
            f'<a class="button button--primary" href="#live">{self.localized_text("hero.cta.live", self.content["meta"]["ui"]["view_live"])}</a>'
            f'<a class="button" href="https://github.com/7SH7">{self.localized_text("hero.cta.code", self.content["meta"]["ui"]["view_code"])}</a>'
            '</div>'
            '</div></section>'
        )

    def live_section(self) -> str:
        live = self.content["live_service"]
        sections = self.content["meta"]["sections"]
        evidence = "".join(
            f'<li>{self.localized_text(f"live.evidence.{index}", item)}</li>'
            for index, item in enumerate(live["evidence"])
        )
        stats = "".join(
            '<article class="stat">'
            f'<strong class="stat-value">{esc(stat["value"])}</strong>'
            f'{self.localized("span", f"stat.{index}.label", stat["label"], ATTR_STAT_LABEL)}'
            '</article>'
            for index, stat in enumerate(self.content["stats"])
        )
        stats_aria = self.translated_aria_attrs("stats.label", COPY["stats_label"])
        live_links = [{"label": self.content["meta"]["ui"]["view_live"], "url": live["url"]}]
        architecture_markup = ""
        if architecture := live.get("architecture"):
            architecture_markup = self.architecture_figure(architecture)

        return (
            '<section class="section" id="live"><div class="container">'
            f'{self.section_heading("01", "live", sections["live"], "live_intro")}'
            '<article class="live-card">'
            '<div>'
            f'{self.localized("span", "live.status", live["status"], ATTR_LIVE_BADGE)}'
            f'<h3>{esc(live["name"])}</h3>'
            f'{self.localized("p", "live.tagline", live["tagline"], ATTR_META)}'
            f'{self.localized("p", "live.role", live["role"])}'
            f'{self.localized("p", "live.summary", live["summary"], ATTR_MUTED)}'
            f'{self.tags(live["technologies"])}'
            f'{self.links(live_links, "live", primary=True)}'
            '</div>'
            f'<ul class="evidence-list">{evidence}</ul>'
            '</article>'
            f'{architecture_markup}'
            f'<div class="stats-grid" {stats_aria}>{stats}</div>'
            '</div></section>'
        )

    def architecture_figure(self, architecture: dict[str, Any]) -> str:
        """Render a generalized operating diagram.

        Everything here is deliberately coarse. The diagram states that the
        service runs across two availability zones behind a load balancer and
        that changes reach it through a validated pipeline. It carries no
        subnet layout, no detection stack, no internal identifiers, and no
        automation path, because a published diagram is a permanent one.
        """
        label = architecture["labels"]

        def node(key: str, x: int, y: int, w: int, h: int, sub: str = "") -> str:
            text_y = y + (h // 2) + (0 if not sub else -6)
            body = (
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7"/>'
                + self.localized(
                    "text",
                    f"architecture.{key}",
                    label[key],
                    f'x="{x + w // 2}" y="{text_y}" class="diagram-label"',
                )
            )
            if sub:
                body += (
                    f'<text x="{x + w // 2}" y="{text_y + 19}" class="diagram-sub">{esc(sub)}</text>'
                )
            return f'<g class="diagram-node">{body}</g>'

        def plain(name: str, x: int, y: int, w: int, h: int, sub: str = "") -> str:
            text_y = y + (h // 2) + (0 if not sub else -6)
            body = (
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7"/>'
                f'<text x="{x + w // 2}" y="{text_y}" class="diagram-label">{esc(name)}</text>'
            )
            if sub:
                body += f'<text x="{x + w // 2}" y="{text_y + 19}" class="diagram-sub">{esc(sub)}</text>'
            return f'<g class="diagram-node">{body}</g>'

        def arrow(x1: int, y1: int, x2: int, y2: int) -> str:
            return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="diagram-flow"/>'

        pipeline = (
            plain("GitHub", 24, 26, 150, 54)
            + arrow(174, 53, 218, 53)
            + plain("GitHub Actions", 222, 26, 210, 54, sub=self.plain_text(label["pipeline"]))
            + arrow(432, 53, 476, 53)
            + plain("Terraform", 480, 26, 180, 54, sub=self.plain_text(label["provision"]))
            + arrow(570, 80, 570, 126)
        )

        zones = (
            '<g class="diagram-zone">'
            '<rect x="404" y="150" width="212" height="70" rx="7"/>'
            + self.localized(
                "text", "architecture.zone_a", label["zone_a"], 'x="414" y="170" class="diagram-zone-label"'
            )
            + '</g><g class="diagram-zone">'
            '<rect x="404" y="240" width="212" height="70" rx="7"/>'
            + self.localized(
                "text", "architecture.zone_b", label["zone_b"], 'x="414" y="260" class="diagram-zone-label"'
            )
            + '</g>'
            + node("app", 420, 178, 180, 34)
            + node("app", 420, 268, 180, 34)
        )

        region = (
            '<g class="diagram-region">'
            '<rect x="16" y="126" width="868" height="208" rx="10"/>'
            + self.localized(
                "text", "architecture.region", label["region"], 'x="32" y="148" class="diagram-region-label"'
            )
            + '</g>'
            + node("balancer", 176, 212, 180, 44)
            + zones
            + node("database", 652, 212, 200, 44, sub="Multi-AZ")
            + arrow(356, 234, 400, 200)
            + arrow(356, 234, 400, 268)
            + arrow(620, 200, 648, 230)
            + arrow(620, 268, 648, 238)
        )

        entry = node("users", 16, 356, 150, 44) + arrow(170, 378, 250, 378) + arrow(266, 370, 266, 260)

        diagram = (
            '<svg class="architecture-diagram" viewBox="0 0 900 410" role="img" '
            f'{self.translated_aria_attrs("architecture.alt", architecture["caption"])}>'
            '<defs><marker id="diagram-arrow" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            '<path d="M0 0 L10 5 L0 10 z"/></marker></defs>'
            f'{pipeline}{region}{entry}'
            '<text x="16" y="404" class="diagram-sub diagram-note">HTTPS</text>'
            '</svg>'
        )

        caption = self.localized(
            "figcaption",
            "live.architecture.caption",
            architecture["caption"],
            'id="micemore-architecture-caption"',
        )
        return (
            '<details class="architecture-disclosure" id="micemore-architecture">'
            f'<summary>{self.localized_text("live.architecture.title", architecture["title"])}</summary>'
            f'<figure class="architecture-figure">{diagram}{caption}</figure>'
            '</details>'
        )

    @staticmethod
    def plain_text(value: dict[str, str]) -> str:
        return value["ko"]

    def experience_section(self) -> str:
        sections = self.content["meta"]["sections"]
        items: list[str] = []
        for index, item in enumerate(self.content["experience"]):
            item_id = item["id"]
            period = item["period"]["display"]
            items.append(
                '<article class="timeline-item">'
                '<div>'
                f'{self.localized("time", f"experience.{item_id}.period", period, ATTR_TIMELINE_DATE)}'
                '</div><div>'
                f'{self.localized("h3", f"experience.{item_id}.organization", item["organization"])}'
                f'{self.localized("p", f"experience.{item_id}.role", item["role"], ATTR_META)}'
                f'{self.localized("p", f"experience.{item_id}.summary", item["summary"])}'
                f'{self.links(item.get("links"), f"experience.{item_id}")}'
                '</div></article>'
            )
        trace = (
            '<svg class="step-trace" viewBox="0 0 216 32" aria-hidden="true" focusable="false">'
            '<path d="M0 27 H38 V21 H78 V15 H119 V9 H160 V3 H216"/></svg>'
        )
        return (
            '<section class="section" id="experience"><div class="container">'
            f'{self.section_heading("02", "experience", sections["experience"], "experience_intro")}'
            f'{trace}<div class="timeline">{"".join(items)}</div>'
            '</div></section>'
        )

    def project_card(self, project: dict[str, Any], compact: bool = False) -> str:
        project_id = project["id"]
        categories = project["categories"]
        highlights = project.get("highlights", [])
        evidence = ""
        if highlights:
            evidence = '<ul class="evidence-list">' + "".join(
                f'<li>{self.localized_text(f"project.{project_id}.highlight.{index}", value)}</li>'
                for index, value in enumerate(highlights)
            ) + "</ul>"
        period = ""
        if project.get("period"):
            period = self.localized(
                "span",
                f"project.{project_id}.period",
                project["period"]["display"],
            )
        role = self.localized_text(f"project.{project_id}.role", project["role"])
        meta = " · ".join(part for part in (period, role) if part)
        recognition = ""
        if project.get("recognition"):
            recognition = self.localized(
                "span",
                f"project.{project_id}.recognition",
                project["recognition"],
                'class="badge badge--accent"',
            )
        classes = "project-card"
        if compact:
            classes += " project-card--compact"
        project_name = self.localized(
            "span",
            f"project.{project_id}.name",
            project["name"],
            'class="project-title" role="heading" aria-level="4"',
        )
        project_outcome = self.localized(
            "span",
            f"project.{project_id}.summary",
            project["summary"],
            'class="project-outcome"',
        )
        project_more = self.localized(
            "span",
            f"project.{project_id}.details",
            self.content["meta"]["ui"]["details"],
            'class="project-more"',
        )
        return (
            f'<details class="{classes}" data-project-categories="{esc(" ".join(categories))}">'
            '<summary class="project-overview">'
            f'{project_name}{project_outcome}{project_more}'
            '</summary><div class="project-detail">'
            f'{self.category_badges(categories, f"project.{project_id}")}'
            f'{recognition}<p class="meta">{meta}</p>'
            f'{evidence}'
            f'{self.tags(project.get("technologies", []))}'
            f'{self.links(project.get("links"), f"project.{project_id}")}'
            '</div></details>'
        )

    def repository_card(self, repository: dict[str, Any], index: int) -> str:
        categories = repository["categories"]
        kind = repository.get("kind", "original")
        kind_label = self.content["meta"]["ui"]["fork" if kind == "fork" else "original"]
        language = f'<span class="tag">{esc(repository["language"])}</span>' if repository.get("language") else ""
        return (
            f'<article class="card repo-card" data-project-categories="{esc(" ".join(categories))}">'
            '<div class="tag-list">'
            f'{self.localized("span", f"repository.{index}.kind", kind_label, ATTR_BADGE)}'
            f'{language}'
            '</div>'
            f'<h3><code>{esc(repository["name"])}</code></h3>'
            f'{self.localized("p", f"repository.{index}.description", repository["description"])}'
            '<div class="actions">'
            f'<a class="button" href="{esc(repository["url"])}">{self.localized_text(f"repository.{index}.open", COPY["open_repository"])}</a>'
            '</div></article>'
        )

    def screens_strip(self) -> str:
        """A row of real screens, so the page has something to look at.

        Four of these projects shipped a front end worth showing; the rest are
        backend or embedded work with no screen to photograph. Rather than let
        that unevenness show up as cards with and without images, the screens
        sit together in one strip above the grid.
        """
        screenshots = self.content.get("screenshots") or []
        if not screenshots:
            return ""
        items = "".join(
            '<figure class="screen">'
            f'<a href="{esc(shot["url"])}" target="_blank" rel="noopener">'
            f'<img src="{esc(shot["src"])}" alt="" width="1200" height="600" loading="lazy" decoding="async">'
            '</a><figcaption>'
            + self.localized("strong", f"screen.{index}.label", shot["label"])
            + self.localized("span", f"screen.{index}.caption", shot["caption"], ATTR_META)
            + '</figcaption></figure>'
            for index, shot in enumerate(screenshots)
        )
        return (
            f'{self.localized("h3", "projects.screens.heading", COPY["screens_heading"])}'
            f'<div class="screen-grid">{items}</div>'
        )

    def projects_section(self) -> str:
        sections = self.content["meta"]["sections"]
        labels = self.content["meta"]["category_labels"]
        filters = "".join(
            f'<button type="button" data-filter="{esc(category)}" aria-pressed="{str(category == "all").lower()}">'
            f'{self.localized_text(f"filter.{category}", labels[category])}</button>'
            for category in ("all", "cloud", "embedded", "backend", "ai-data")
        )
        filter_aria = self.translated_aria_attrs("filter.label", COPY["filter_label"])
        self.add_translation("filter.status", COPY["filter_status"])

        featured = sorted(
            self.content["featured_projects"],
            key=lambda project: FEATURED_ORDER.index(project["id"]),
        )
        featured_cards = "".join(self.project_card(project) for project in featured)
        additional_cards = "".join(self.project_card(project, compact=True) for project in self.content["other_projects"])
        repositories = "".join(
            self.repository_card(repository, index)
            for index, repository in enumerate(self.content["repository_links"])
        )
        return (
            '<section class="section" id="projects"><div class="container">'
            f'{self.section_heading("03", "projects", sections["projects"], "projects_intro")}'
            f'<div class="project-filters" {filter_aria}>{filters}</div>'
            '<p class="sr-only" aria-live="polite" data-filter-status data-i18n="filter.status">'
            f'{esc(COPY["filter_status"]["ko"])}</p>'
            f'{self.screens_strip()}'
            f'{self.localized("h3", "projects.featured.heading", COPY["featured_projects"])}'
            f'<div class="project-grid">{featured_cards}</div>'
            '<details class="more-disclosure">'
            f'<summary>{self.localized_text("projects.more.summary", COPY["more_projects_summary"])}</summary>'
            '<div class="more-disclosure-body">'
            f'{self.localized("h3", "projects.additional.heading", COPY["additional_projects"])}'
            f'<div class="compact-grid">{additional_cards}</div>'
            '<hr>'
            f'{self.localized("h3", "projects.repositories.heading", sections["repositories"])}'
            f'{self.localized("p", "projects.repositories.intro", COPY["repositories_intro"], ATTR_SECTION_INTRO)}'
            f'<div class="compact-grid repo-grid">{repositories}</div>'
            '</div></details>'
            '</div></section>'
        )

    def awards_section(self) -> str:
        sections = self.content["meta"]["sections"]
        headers = (COPY["table_period"], COPY["table_award"], COPY["table_issuer"], COPY["table_evidence"])
        head = "".join(
            self.localized("th", f"awards.header.{index}", value, 'scope="col"')
            for index, value in enumerate(headers)
        )
        rows: list[str] = []
        for index, award in enumerate(self.content["awards"]):
            rows.append(
                '<tr>'
                f'<td {self.translated_label_attrs("awards.label.period", headers[0])}>{esc(award["date"])}</td>'
                f'<td {self.translated_label_attrs("awards.label.title", headers[1])}>{self.localized_text(f"award.{index}.title", award["title"])}</td>'
                f'<td {self.translated_label_attrs("awards.label.issuer", headers[2])}>{self.localized_text(f"award.{index}.issuer", award["issuer"])}</td>'
                f'<td {self.translated_label_attrs("awards.label.context", headers[3])}>{self.localized_text(f"award.{index}.context", award["context"])}</td>'
                '</tr>'
            )
        return (
            '<section class="section" id="awards"><div class="container">'
            f'{self.section_heading("04", "awards", sections["awards"], "awards_intro")}'
            '<div class="table-wrap"><table class="responsive-table">'
            f'<thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody>'
            '</table></div></div></section>'
        )

    def activities_section(self) -> str:
        sections = self.content["meta"]["sections"]
        headers = (COPY["table_period"], COPY["table_activity"], COPY["table_organization"], COPY["table_details"])
        head = "".join(
            self.localized("th", f"activities.header.{index}", value, 'scope="col"')
            for index, value in enumerate(headers)
        )
        rows: list[str] = []
        for index, activity in enumerate(self.content["activities"]):
            period = "—"
            if activity.get("period"):
                period = self.localized_text(f"activity.{index}.period", activity["period"]["display"])
            organization = "—"
            if activity.get("organization"):
                organization = self.localized_text(f"activity.{index}.organization", activity["organization"])
            description = self.localized_text(f"activity.{index}.description", activity["description"])
            description += self.links(activity.get("links"), f"activity.{index}")
            rows.append(
                '<tr>'
                f'<td {self.translated_label_attrs("activities.label.period", headers[0])}>{period}</td>'
                f'<td {self.translated_label_attrs("activities.label.name", headers[1])}>{self.localized_text(f"activity.{index}.name", activity["name"])}</td>'
                f'<td {self.translated_label_attrs("activities.label.organization", headers[2])}>{organization}</td>'
                f'<td {self.translated_label_attrs("activities.label.details", headers[3])}>{description}</td>'
                '</tr>'
            )
        return (
            '<section class="section" id="activities"><div class="container">'
            f'{self.section_heading("05", "activities", sections["activities"], "activities_intro")}'
            '<details class="more-disclosure">'
            f'<summary>{self.localized_text("activities.more.summary", COPY["more_activities_summary"])}</summary>'
            '<div class="more-disclosure-body">'
            '<div class="table-wrap"><table class="responsive-table">'
            f'<thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody>'
            '</table></div>'
            '</div></details>'
            '</div></section>'
        )

    def skills_section(self) -> str:
        sections = self.content["meta"]["sections"]
        headers = (COPY["table_category"], COPY["table_stack"], COPY["table_context"])
        head = "".join(
            self.localized("th", f"skills.header.{index}", value, 'scope="col"')
            for index, value in enumerate(headers)
        )
        rows: list[str] = []
        for index, skill in enumerate(self.content["skills"]):
            rows.append(
                '<tr>'
                f'<td {self.translated_label_attrs("skills.label.category", headers[0])}>{self.localized_text(f"skill.{index}.label", skill["label"])}</td>'
                f'<td {self.translated_label_attrs("skills.label.stack", headers[1])}>{self.tags(skill["items"])}</td>'
                f'<td {self.translated_label_attrs("skills.label.context", headers[2])}>{self.localized_text(f"skill.{index}.context", skill["context"])}</td>'
                '</tr>'
            )
        return (
            '<section class="section" id="skills"><div class="container">'
            f'{self.section_heading("06", "skills", sections["skills"], "skills_intro")}'
            '<div class="table-wrap"><table class="responsive-table">'
            f'<thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody>'
            '</table></div></div></section>'
        )

    def education_section(self) -> str:
        sections = self.content["meta"]["sections"]
        education = self.content["education"]
        credentials = self.content["credentials"]
        certifications = "".join(
            f'<li>{self.localized_text(f"credential.certification.{index}", item["name"])}</li>'
            for index, item in enumerate(credentials["certifications"])
        )
        languages = "".join(
            f'<li><strong>{esc(item["name"])}</strong> · {esc(item["score"])}'
            f'{" · " + esc(item["date"]) if item.get("date") else ""}</li>'
            for item in credentials["languages"]
        )
        language_block = ""
        if languages:
            language_block = (
                self.localized("h3", "credentials.languages", COPY["languages"])
                + f"<ul>{languages}</ul>"
            )
        return (
            '<section class="section" id="education"><div class="container">'
            f'{self.section_heading("07", "education", sections["education"], "education_intro")}'
            '<div class="split-grid">'
            '<article class="panel">'
            f'{self.localized("p", "education.card.label", COPY["education_card"], ATTR_EYEBROW)}'
            f'{self.localized("h3", "education.institution", education["institution"])}'
            f'{self.localized("p", "education.major", education["major"])}'
            '</article>'
            '<article class="panel">'
            f'{self.localized("p", "credentials.card.label", COPY["credentials_card"], ATTR_EYEBROW)}'
            f'{self.localized("h3", "credentials.certifications", COPY["certifications"])}'
            f'<ul>{certifications}</ul>'
            f'{language_block}'
            f'{self.localized("p", "credentials.military", credentials["military"], ATTR_MUTED)}'
            '</article>'
            '</div></div></section>'
        )

    def contact_section(self) -> str:
        sections = self.content["meta"]["sections"]
        cards: list[str] = []
        for index, contact in enumerate(self.content["contacts"]):
            pending = ""
            if contact.get("placeholder"):
                pending = self.localized(
                    "span",
                    f"contact.{index}.pending",
                    COPY["pending_value"],
                    'class="badge badge--accent"',
                )
            cards.append(
                '<article class="card">'
                f'{self.localized("p", f"contact.{index}.label", contact["label"], ATTR_EYEBROW)}'
                f'<a href="{esc(contact["url"])}">{esc(contact["value"])}</a>'
                f'{pending}'
                '</article>'
            )
        return (
            '<section class="section" id="contact"><div class="container">'
            f'{self.section_heading("08", "contact", sections["contact"], "contact_intro")}'
            f'<div class="compact-grid">{"".join(cards)}</div>'
            '</div></section>'
        )

    def body(self) -> str:
        return (
            f'{self.header()}<main id="main-content">'
            f'{self.hero()}{self.live_section()}{self.experience_section()}'
            f'{self.projects_section()}{self.awards_section()}{self.activities_section()}'
            f'{self.skills_section()}{self.education_section()}{self.contact_section()}'
            '</main>'
        )


def validate_content(content: dict[str, Any]) -> None:
    expected_counts = {
        "experience": 5,
        "featured_projects": 7,
        "other_projects": 6,
        "activities": 10,
    }
    for key, expected in expected_counts.items():
        actual = len(content.get(key, []))
        if actual != expected:
            raise ValueError(f"{key}: expected {expected}, found {actual}")
    if len(content.get("awards", [])) < 7:
        raise ValueError("At least seven verified awards are required")

    for project in content["featured_projects"] + content["other_projects"]:
        categories = set(project.get("categories", []))
        if not categories or not categories <= PROJECT_CATEGORIES:
            raise ValueError(f"Invalid categories on project {project.get('id')}: {sorted(categories)}")

    def walk(value: Any, path: str = "root") -> None:
        if isinstance(value, dict):
            if "ko" in value:
                missing = set(LANGUAGES) - set(value)
                if missing:
                    raise ValueError(f"Missing locale at {path}: {', '.join(sorted(missing))}")
            for key, nested in value.items():
                walk(nested, f"{path}.{key}")
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                walk(nested, f"{path}[{index}]")

    walk(content)

    for contact in content["contacts"]:
        url = contact["url"]
        if not (url.startswith("https://") or url.startswith("mailto:")):
            raise ValueError(f"Unsupported contact URL: {url}")

    architecture_src = content["live_service"].get("architecture", {}).get("src")
    if architecture_src and not (ROOT / architecture_src).is_file():
        raise ValueError(f"Architecture image not found: {architecture_src}")

    for shot in content.get("screenshots") or []:
        if not (ROOT / shot["src"]).is_file():
            raise ValueError(f"Screenshot not found: {shot['src']}")


def validate_output(document: str) -> None:
    required = (
        '<html lang="ko">',
        'id="live"',
        'id="experience"',
        'id="projects"',
        'id="awards"',
        'id="activities"',
        'id="skills"',
        'id="education"',
        'id="contact"',
        'data-filter="embedded"',
        'https://m.micemore.com/',
        'kimseunghwan7777@gmail.com',
    )
    missing = [needle for needle in required if needle not in document]
    if missing:
        raise ValueError(f"Generated HTML is missing required content: {missing}")

    prohibited = (
        "GPA",
        "TOE" + "IC",
        "전공 " + "평점",
        "백분위",
        "AI Dev" + "Ops",
        "assume" + "_role",
        "agent-" + "readonly",
        "Event" + "Bridge",
        "AIDEVOPS" + "_LIVE",
        "architecture.png",
        "정확도 30" + "% 향상",
        "정보처리" + "기사" + " 필기",
        "AWS " + "SAA" + " 준비",
        "Azu" + "re",
        "/v1/" + "taps",
        "10.20." + "0.0" + "/16",
        "micemore" + ".dev",
        "walking-" + "library",
        "pubsub-" + "choreography-with-idempotency",
    )
    found = [term for term in prohibited if term in document]
    if found:
        raise ValueError(f"Generated HTML contains prohibited material: {found}")


def build(offline: bool) -> str:
    content = load_json(CONTENT_PATH)
    validate_content(content)

    repo_stat = next(stat for stat in content["stats"] if stat.get("source") == "GitHub API")
    repo_stat["value"] = str(fetch_public_repo_count(int(repo_stat["value"]), offline))

    renderer = Renderer(content)
    body = renderer.body()
    renderer.add_translation("skip_to_content", COPY["skip_to_content"])

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    replacements = {
        "{{PAGE_TITLE}}": esc(content["meta"]["site_title"]["ko"]),
        "{{META_DESCRIPTION}}": esc(content["meta"]["description"]["ko"]),
        "{{BODY}}": body,
        "{{TRANSLATIONS_JSON}}": json.dumps(
            renderer.translations,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).replace("<", "\\u003c"),
    }
    for placeholder, replacement in replacements.items():
        if placeholder not in template:
            raise ValueError(f"Template placeholder missing: {placeholder}")
        template = template.replace(placeholder, replacement)
    if any(placeholder in template for placeholder in replacements):
        raise ValueError("Unresolved template placeholder in generated HTML")
    validate_output(template)
    return template


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify index.html matches a fresh build")
    parser.add_argument("--offline", action="store_true", help="skip the GitHub API and use the stored fallback")
    args = parser.parse_args()

    document = build(args.offline)
    if args.check:
        if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text(encoding="utf-8") != document:
            print("index.html is stale; run: python build.py", file=sys.stderr)
            return 1
        print("index.html is current and validated")
        return 0

    OUTPUT_PATH.write_text(document, encoding="utf-8", newline="\n")
    print(f"built {OUTPUT_PATH.name} ({len(document):,} characters)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
