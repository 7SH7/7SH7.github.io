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
    "micemore",
    "unibloom",
    "llm-for-science",
    "ugly-pick",
    "vehicle-diagnostics-r300",
)
ATTR_SECTION_INTRO = 'class="section-intro"'
ATTR_EYEBROW = 'class="eyebrow"'
ATTR_HERO_LEDE = 'class="hero-lede"'
ATTR_BADGE = 'class="badge"'
ATTR_STAT_LABEL = 'class="stat-label"'
ATTR_LIVE_BADGE = 'class="badge badge--live"'
ATTR_META = 'class="meta"'
ATTR_DIALOG_LEDE = 'class="dialog-lede"'
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
        "ko": "BACKEND · CLOUD · AI SERVICE",
        "ja": "BACKEND · CLOUD · AI SERVICE",
        "en": "BACKEND · CLOUD · AI SERVICE",
    },
    "live_intro": {
        "ko": "MICEMore를 서울 리전에서 직접 운영하며, 배포 구조와 부하 테스트 결과, 장애 대응 방식을 실제 운영 기준으로 정리했습니다.",
        "ja": "MICEMoreをソウルリージョンで自ら運用し、デプロイ構成・負荷テスト結果・障害対応の方式を実運用の基準でまとめました。",
        "en": "I run MICEMore in the AWS Seoul Region myself; this section covers its deployment setup, load test results, and incident handling as they work in production.",
    },
    "stats_label": {"ko": "핵심 수치", "ja": "主要指標", "en": "Key metrics"},
    "experience_intro": {
        "ko": "행사용 AI 서비스 창업팀의 개발 총괄을 비롯해, 오픈소스 논문 데이터 정제, 대학 학사 데이터 품질 개선, KISTI 업무시스템 개발까지 맡은 일과 결과를 정리했습니다.",
        "ja": "イベント向けAIサービス創業チームの開発統括をはじめ、オープンソースの論文データ精製、大学の学事データ品質改善、KISTI業務システム開発まで、担当業務と成果をまとめました。",
        "en": "From leading development at an event AI startup to open-source paper-data curation, university academic data quality work, and building a KISTI business system, here is what I owned and what came of it.",
    },
    "projects_intro": {
        "ko": "AWS 서울 리전에서 단독 운영 중인 행사용 AI 통합 서비스를 비롯해, 인프라 코드 관리와 Spring Boot 백엔드, 캐시 전략, 다중 모델 워크플로우까지 프로젝트별 역할과 결과를 정리했습니다.",
        "ja": "AWSソウルリージョンで単独運用中のイベント向けAI統合サービスをはじめ、インフラのコード管理、Spring Bootバックエンド、キャッシュ戦略、マルチモデルワークフローまで、プロジェクトごとの役割と成果をまとめました。",
        "en": "From an event AI service I run solo in the AWS Seoul Region to infrastructure as code, Spring Boot backends, caching strategy, and multi-model workflows, each project lists my role and its results.",
    },
    "featured_projects": {"ko": "대표 프로젝트", "ja": "主要プロジェクト", "en": "Featured projects"},
    "additional_projects": {"ko": "추가 프로젝트", "ja": "その他のプロジェクト", "en": "Additional projects"},
    "more_projects_summary": {
        "ko": "추가 프로젝트 보기",
        "ja": "その他のプロジェクトを見る",
        "en": "View additional projects",
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
        "ko": "MICEMore로 선정된 관광 창업 지원사업을 비롯해, 주최와 대상, 순위를 확인할 수 있는 수상·선정 이력을 정리했습니다.",
        "ja": "MICEMoreで選定された観光創業支援事業をはじめ、主催・対象・順位を確認できる受賞・選定歴をまとめました。",
        "en": "Including the tourism startup programs MICEMore was selected for, these are awards and selections with a verifiable organizer, project, and placement.",
    },
    "activities_intro": {
        "ko": "AI 시스템반도체 과정과 AWS Academy를 비롯해, PyTorch 문서 한글화 기여와 신입 멘토링까지 배우고 나눈 활동을 정리했습니다.",
        "ja": "AIシステム半導体課程とAWS Academyをはじめ、PyTorchドキュメントの韓国語化への貢献や新入メンバーのメンタリングまで、学びと共有の活動をまとめました。",
        "en": "From the AI system semiconductor program and AWS Academy to PyTorch documentation translation and mentoring new members, these are the ways I have learned and shared.",
    },
    "skills_intro": {
        "ko": "Spring Boot 백엔드부터 AWS·Terraform 인프라, STM32 펌웨어까지, 기술마다 실제로 사용한 맥락을 함께 정리했습니다.",
        "ja": "Spring BootバックエンドからAWS・Terraformインフラ、STM32ファームウェアまで、技術ごとに実際に使った文脈を併せてまとめました。",
        "en": "From Spring Boot backends to AWS and Terraform infrastructure and STM32 firmware, each technology is listed with the context I used it in.",
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

    def section_heading(self, number: str, key: str, title: dict[str, str], intro_key: str | None = None) -> str:
        return (
            '<div class="section-heading">'
            '<div>'
            f'<p class="section-label">{esc(number)} // {esc(key.upper())}</p>'
            f'{self.localized("h2", f"section.{key}.title", title)}'
            '</div>'
            f'{self.localized("p", f"section.{key}.intro", COPY[intro_key], ATTR_SECTION_INTRO) if intro_key else ""}'
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

    def screenshot_for(self, project_id: str) -> dict[str, Any] | None:
        for shot in self.content.get("screenshots") or []:
            if shot.get("project") == project_id:
                return shot
        return None

    def project_card(self, project: dict[str, Any], compact: bool = False) -> tuple[str, str]:
        """Return the grid card and the dialog it opens.

        The card carries only what is worth scanning: the name and the outcome.
        Everything else lives in the dialog, so opening one project no longer
        pushes the rest of the grid down the page.
        """
        project_id = project["id"]
        dialog_id = f"project-{project_id}"
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
        case_study = ""
        for index, section in enumerate(project.get("sections", [])):
            prefix = f"project.{project_id}.section.{index}"
            heading = self.localized_text(f"{prefix}.title", section["title"])
            items = "".join(
                f'<li>{self.localized_text(f"{prefix}.item.{item_index}", item)}</li>'
                for item_index, item in enumerate(section["items"])
            )
            case_study += f'<details><summary>{heading}</summary><ul class="evidence-list">{items}</ul></details>'
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
            'class="project-title"',
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
        figure = ""
        if shot := self.screenshot_for(project_id):
            figure = (
                '<div class="dialog-figure">'
                f'<img src="{esc(shot["src"])}" alt="" width="1200" height="600" loading="lazy" decoding="async">'
                '</div>'
            )
        card = (
            f'<article class="{classes}" data-project-categories="{esc(" ".join(categories))}">'
            f'<button type="button" class="project-overview" data-open-dialog="{dialog_id}">'
            f'{project_name}{project_outcome}{project_more}'
            '</button></article>'
        )
        title = self.localized(
            "h3",
            f"project.{project_id}.name",
            project["name"],
            f'id="{dialog_id}-title"',
        )
        dialog = (
            f'<dialog class="project-dialog" id="{dialog_id}" aria-labelledby="{dialog_id}-title">'
            '<form method="dialog" class="dialog-dismiss">'
            f'<button type="submit" {self.translated_aria_attrs(f"project.{project_id}.close", self.content["meta"]["ui"]["close"])}>&times;</button>'
            '</form>'
            f'{figure}'
            '<div class="dialog-body">'
            f'{self.category_badges(categories, f"dialog.{project_id}")}'
            f'{title}'
            f'{recognition}<p class="meta">{meta}</p>'
            f'{self.localized("p", f"dialog.{project_id}.summary", project["summary"], ATTR_DIALOG_LEDE)}'
            f'{evidence}'
            f'{case_study}'
            f'{self.tags(project.get("technologies", []))}'
            f'{self.links(project.get("links"), f"dialog.{project_id}")}'
            '</div></dialog>'
        )
        return card, dialog

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
        dialogs: list[str] = []
        featured_cards = ""
        for project in featured:
            card, dialog = self.project_card(project)
            featured_cards += card
            dialogs.append(dialog)
        additional_cards = ""
        for project in self.content["other_projects"]:
            card, dialog = self.project_card(project, compact=True)
            additional_cards += card
            dialogs.append(dialog)
        return (
            '<section class="section" id="projects"><div class="container">'
            f'{self.section_heading("03", "projects", sections["projects"], "projects_intro")}'
            f'<div class="project-filters" {filter_aria}>{filters}</div>'
            '<p class="sr-only" aria-live="polite" data-filter-status data-i18n="filter.status">'
            f'{esc(COPY["filter_status"]["ko"])}</p>'
            f'{self.localized("h3", "projects.featured.heading", COPY["featured_projects"])}'
            f'<div class="project-grid">{featured_cards}</div>'
            '<details class="more-disclosure">'
            f'<summary>{self.localized_text("projects.more.summary", COPY["more_projects_summary"])}</summary>'
            '<div class="more-disclosure-body">'
            f'{self.localized("h3", "projects.additional.heading", COPY["additional_projects"])}'
            f'<div class="compact-grid">{additional_cards}</div>'
            '</div></details>'
            f'{"".join(dialogs)}'
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
            f'{self.section_heading("07", "education", sections["education"])}'
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
            f'{self.section_heading("08", "contact", sections["contact"])}'
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
        "featured_projects": 5,
        "other_projects": 9,
        "activities": 10,
        # External organizers only; on-campus and club wins were removed
        # deliberately, so a change here should be deliberate too.
        "awards": 5,
    }
    for key, expected in expected_counts.items():
        actual = len(content.get(key, []))
        if actual != expected:
            raise ValueError(f"{key}: expected {expected}, found {actual}")

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
        'id="project-unibloom"',
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
        "micemore-" + "prod",
        "micemore-" + "login",
        "REPLACE" + "_ME",
        "SECURITY_" + "BACKLOG",
        "LOADTEST_" + "PLAN",
        "bas" + "tion",
        "actuator/" + "health",
        "ELEVEN" + "LABS",
        "flyway_schema_" + "history",
        "image-" + "tag",
        "포트폴리오 " + "해커톤 대상",
        "홀리데이 " + "해커톤 대상",
        "한동" + "대 SW",
        "한동" + "대 데이터",
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
