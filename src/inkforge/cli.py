"""Rich Typer CLI for InkForge (墨铸)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Literal

import typer
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from inkforge import __version__
from inkforge.analyzer.slop_detector import analyze_prose
from inkforge.config import load_settings
from inkforge.engine.exporter import export_project
from inkforge.engine.pipeline import NovelPipeline
from inkforge.genres.blueprints import get_genre, list_genres
from inkforge.llm import create_llm_client
from inkforge.storage.repository import NovelRepository
from inkforge.web.app import create_app

app = typer.Typer(
    name="inkforge",
    help="墨铸 InkForge — 多题材、强逻辑、去AI味的小说创作引擎与编辑工作室",
    no_args_is_help=True,
)
console = Console()


def _parse_chapter_range(spec: str) -> list[int]:
    nums: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            nums.extend(range(int(a.strip()), int(b.strip()) + 1))
        else:
            nums.append(int(part))
    return sorted(set(n for n in nums if n >= 1))


def _print_audit(report) -> None:
    m = report.metrics
    color = "green" if m.humanity_score >= 78 else ("yellow" if m.humanity_score >= 60 else "red")
    console.print(
        Panel(
            f"[bold {color}]文笔自然度：{m.humanity_score}/100（{m.grade} 级）[/bold {color}]  |  "
            f"AI味风险：[bold]{m.ai_risk_score}[/bold]  |  "
            f"字数：{m.char_count}  |  "
            f"句式呼吸感：{m.burstiness_score}/100  |  "
            f"对话占比：{int(m.dialogue_ratio * 100)}%\n"
            f"{report.summary}",
            title="红笔去AI味体检报告",
            border_style=color,
        )
    )
    if report.slop_issues:
        tbl = Table(title=f"检出红笔批注（共 {len(report.slop_issues)} 处）", show_lines=True)
        tbl.add_column("行号", style="dim", width=6)
        tbl.add_column("类别", width=16)
        tbl.add_column("级别", width=8)
        tbl.add_column("原文命中片段", style="bold red")
        tbl.add_column("修改建议")
        for item in report.slop_issues[:20]:
            tbl.add_row(
                str(item.line),
                item.category,
                item.severity,
                item.phrase,
                item.suggestion,
            )
        console.print(tbl)


@app.command()
def version() -> None:
    """显示版本号与当前模型配置。"""
    settings = load_settings()
    r = settings.llm.resolved()
    console.print(f"[bold]InkForge 墨铸[/bold] v{__version__}  |  Provider: {r.provider} ({r.model})")


@app.command()
def genres() -> None:
    """列出全部内置小说题材蓝图。"""
    table = Table(title="InkForge 内置 10 大题材创作蓝图", show_lines=True)
    table.add_column("ID", style="bold cyan", width=18)
    table.add_column("题材名称", style="bold", width=20)
    table.add_column("叙事与风格锚点")
    table.add_column("默认章字数", justify="right", width=10)
    for g in list_genres():
        table.add_row(g.id, g.name, g.tagline, str(g.default_words_per_chapter))
    console.print(table)


@app.command()
def init(
    title: str = typer.Option(..., "--title", "-t", help="小说书名"),
    genre: str = typer.Option("suspense", "--genre", "-g", help="题材 ID（运行 inkforge genres 查看）"),
    premise: str = typer.Option(..., "--premise", "-p", help="核心故事创意/前提"),
    chapters: int = typer.Option(6, "--chapters", "-c", help="规划总章节数"),
    style: str = typer.Option("", "--style", "-s", help="补充文风偏好"),
    plan_now: bool = typer.Option(True, "--plan/--no-plan", help="创建后立即生成故事圣经与大纲"),
) -> None:
    """新建一部小说项目并生成故事圣经（世界观铁律、人物声纹卡、伏笔与大纲）。"""
    get_genre(genre)
    settings = load_settings()
    repo = NovelRepository(settings.db_path)
    pipeline = NovelPipeline(create_llm_client(settings.llm), repo)

    project = pipeline.create_project(
        title=title,
        genre_id=genre,
        premise=premise,
        style_notes=style,
        target_chapters=chapters,
    )
    console.print(f"[green]已创建项目[/green]：{project.title}（ID: [bold]{project.id}[/bold]）")

    if plan_now:
        async def _run() -> None:
            def _cb(stage: str, msg: str) -> None:
                console.print(f"[cyan][{stage}][/cyan] {msg}")

            await pipeline.build_story_bible(project.id, on_progress=_cb)

        asyncio.run(_run())
        console.print(f"\n下一步：运行 [bold]inkforge write {project.id} --chapters 1-2[/bold] 开始创作。")


@app.command()
def write(
    project_id: str = typer.Argument(..., help="项目 ID"),
    chapters: str = typer.Option("1", "--chapters", "-c", help="章号或范围，如 1 或 1-3"),
    mode: Literal["craft", "fast"] = typer.Option("craft", "--mode", "-m", help="craft=全链路精工 / fast=快速模式"),
) -> None:
    """按章运行「分镜 → 初稿 → 去AI体检 → 精修 → 状态同步」创作流水线。"""
    settings = load_settings()
    repo = NovelRepository(settings.db_path)
    pipeline = NovelPipeline(create_llm_client(settings.llm), repo)
    targets = _parse_chapter_range(chapters)

    async def _run() -> None:
        for num in targets:
            console.rule(f"正在生成第 {num} 章（模式：{mode}）")
            ch = await pipeline.generate_chapter(
                project_id,
                num,
                mode=mode,
                on_progress=lambda st, msg: console.print(f"  [cyan]{st}[/cyan] · {msg}"),
            )
            if ch.audit:
                _print_audit(ch.audit)

    asyncio.run(_run())


@app.command()
def audit(
    file_path: Path = typer.Argument(..., exists=True, readable=True, help="待体检的 txt/md 小说文件"),
    genre: str | None = typer.Option(None, "--genre", "-g", help="可选题材 ID，用于叠加题材烂梗检测"),
) -> None:
    """对任意本地文本执行离线「去AI味红笔体检」（0 Token、毫秒级）。"""
    text = file_path.read_text(encoding="utf-8")
    report = analyze_prose(text, genre_id=genre)
    _print_audit(report)


@app.command()
def polish(
    file_path: Path = typer.Argument(..., exists=True, readable=True, help="待精修的小说草稿文件"),
    genre: str = typer.Option("suspense", "--genre", "-g", help="题材 ID"),
    output: Path | None = typer.Option(None, "--output", "-o", help="保存精修结果的路径"),
) -> None:
    """对任意章节草稿执行「去AI味外科手术精修」并展示前后分数对比。"""
    settings = load_settings()
    repo = NovelRepository(settings.db_path)
    pipeline = NovelPipeline(create_llm_client(settings.llm), repo)
    text = file_path.read_text(encoding="utf-8")

    result = asyncio.run(pipeline.polish_standalone_text(text, genre_id=genre))
    before_s = result["before_audit"]["metrics"]["humanity_score"]
    after_s = result["after_audit"]["metrics"]["humanity_score"]
    delta = result["score_delta"]
    sign = "+" if delta >= 0 else ""

    console.print(
        Panel(
            f"自然度变化：[bold]{before_s}[/bold] → [bold green]{after_s}[/bold green]（{sign}{delta} 分）",
            title="去AI味精修完成",
            border_style="green",
        )
    )
    if output:
        output.write_text(result["polished_text"], encoding="utf-8")
        console.print(f"已写入：[bold]{output}[/bold]")
    else:
        console.print(result["polished_text"])


@app.command()
def export(
    project_id: str = typer.Argument(..., help="项目 ID"),
    fmt: Literal["md", "txt", "html", "epub"] = typer.Option("epub", "--format", "-f", help="导出格式：md|txt|html|epub"),
    output_dir: Path = typer.Option(Path("exports"), "--out", "-o", help="导出目录"),
) -> None:
    """将小说导出为 Markdown / TXT / 独立阅读器 HTML / 标准 EPUB3 电子书。"""
    settings = load_settings()
    repo = NovelRepository(settings.db_path)
    project = repo.get_project(project_id)
    if not project:
        console.print(f"[red]未找到项目：{project_id}[/red]")
        raise typer.Exit(1)
    chapters = repo.list_chapters(project_id)
    out = export_project(project, chapters, output_dir, fmt=fmt)
    console.print(f"[green]导出成功[/green]：{out.resolve()}")


@app.command()
def demo(
    genre: str = typer.Option("suspense", "--genre", "-g", help="演示题材 ID，如 suspense / xianxia / scifi"),
    chapters: int = typer.Option(2, "--chapters", "-c", help="生成演示章节数"),
) -> None:
    """免 API Key 一键跑通完整演示：建档 → 设定集 → 写章 → 去AI体检 → 精修 → 导出 EPUB。"""
    bp = get_genre(genre)
    settings = load_settings()
    settings.llm.provider = "demo"
    repo = NovelRepository(settings.db_path)
    pipeline = NovelPipeline(create_llm_client(settings.llm), repo)

    project = pipeline.create_project(
        title=f"《演示》{bp.name}样本集",
        genre_id=bp.id,
        premise=bp.sample_premise,
        target_chapters=max(4, chapters),
    )

    async def _run() -> None:
        await pipeline.build_story_bible(
            project.id,
            on_progress=lambda st, msg: console.print(f"[cyan]{st}[/cyan] · {msg}"),
        )
        for num in range(1, chapters + 1):
            ch = await pipeline.generate_chapter(
                project.id,
                num,
                mode="craft",
                on_progress=lambda st, msg: console.print(f"  [cyan]{st}[/cyan] · {msg}"),
            )
            if ch.revisions:
                first_s = ch.revisions[0].humanity_score
                last_s = ch.revisions[-1].humanity_score
                console.print(
                    f"[bold green]第 {num} 章完成[/bold green]：初稿 {first_s} 分 → 精修后 {last_s} 分"
                )

    asyncio.run(_run())
    out = export_project(project, repo.list_chapters(project.id), settings.exports_dir, fmt="epub")
    console.print(
        Panel(
            f"项目 ID：{project.id}\n已自动导出 EPUB：{out.resolve()}\n"
            "运行 [bold]inkforge serve[/bold] 可在浏览器工作室查看红笔批注与前后对比！",
            title="InkForge 全链路演示完成",
            border_style="green",
        )
    )


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="监听地址"),
    port: int = typer.Option(8765, "--port", "-p", help="监听端口"),
) -> None:
    """启动墨铸 InkForge 本地 Web 编辑工作室。"""
    settings = load_settings()
    web_app = create_app(settings)
    console.print(
        Panel(
            f"工作室地址：[bold cyan]http://{host}:{port}[/bold cyan]\n"
            f"当前引擎：[bold]{settings.llm.resolved().provider}[/bold] ({settings.llm.resolved().model})\n"
            "可在右上角「模型设置」随时切换 DeepSeek / 豆包 / 通义千问 / OpenAI / Ollama / 离线演示引擎。",
            title="墨铸 InkForge 编辑工作室已启动",
            border_style="cyan",
        )
    )
    uvicorn.run(web_app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    app()
