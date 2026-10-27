import streamlit as st
import pandas as pd
import json
import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta

st.set_page_config(page_title="Кабинет автора", page_icon="✍️", layout="wide")

DATA_FILE = "author_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"books": [], "daily_words": {}, "notes": [], "characters": [], "relations": [], "board": {"ideas": [], "in_progress": [], "done": []}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

st.title("✍️ Кабинет автора")
st.caption("Пишите, отслеживайте прогресс, не теряйте идеи")

menu = st.sidebar.radio(
    "Разделы",
    ["📚 Книги", "👥 Персонажи", "🗂 Доска", "📝 Слова за день", "💡 Заметки", "📊 Статистика", "📰 Новости ИИ"]
)

st.sidebar.divider()
st.sidebar.subheader("💾 Резервная копия")

st.sidebar.download_button(
    label="⬇️ Скачать данные (JSON)",
    data=json.dumps(data, ensure_ascii=False, indent=2),
    file_name=f"author_backup_{date.today()}.json",
    mime="application/json"
)

uploaded = st.sidebar.file_uploader("⬆️ Загрузить данные", type=["json"])
if uploaded is not None:
    try:
        new_data = json.load(uploaded)
        if st.sidebar.button("Подтвердить загрузку"):
            data = new_data
            save_data(data)
            st.sidebar.success("Данные загружены!")
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"Ошибка: {e}")

# ═══════════════════════════════════════
# РАЗДЕЛ 1: КНИГИ
# ═══════════════════════════════════════
if menu == "📚 Книги":
    st.header("Мои книги")

    with st.expander("➕ Добавить новую книгу"):
        with st.form("add_book"):
            title = st.text_input("Название книги")
            genre = st.text_input("Жанр")
            total_chapters = st.number_input("Всего глав (план)", min_value=1, value=10)
            deadline = st.date_input("Дедлайн", value=date.today() + timedelta(days=90))
            submitted = st.form_submit_button("Добавить книгу")
            if submitted and title:
                data["books"].append({
                    "title": title,
                    "genre": genre,
                    "total_chapters": total_chapters,
                    "done_chapters": 0,
                    "deadline": str(deadline),
                    "created": str(date.today())
                })
                save_data(data)
                st.success(f"Книга «{title}» добавлена!")
                st.rerun()

    if not data["books"]:
        st.info("Пока нет книг. Добавьте первую через кнопку выше.")
    else:
        for i, book in enumerate(data["books"]):
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.subheader(book["title"])
                    if book["genre"]:
                        st.caption(f"Жанр: {book['genre']}")
                with col2:
                    progress = book["done_chapters"] / book["total_chapters"] if book["total_chapters"] > 0 else 0
                    st.metric("Главы", f"{book['done_chapters']} / {book['total_chapters']}")
                    st.progress(min(progress, 1.0))
                with col3:
                    deadline = datetime.strptime(book["deadline"], "%Y-%m-%d").date()
                    days_left = (deadline - date.today()).days
                    if days_left < 0:
                        st.error(f"Просрочено на {abs(days_left)} дн.")
                    elif days_left < 7:
                        st.warning(f"Осталось {days_left} дн.")
                    else:
                        st.info(f"Осталось {days_left} дн.")
                    st.caption(f"Дедлайн: {book['deadline']}")

                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button("✅ +1 глава", key=f"plus_{i}"):
                        if book["done_chapters"] < book["total_chapters"]:
                            data["books"][i]["done_chapters"] += 1
                            save_data(data)
                            st.rerun()
                with col_b:
                    if st.button("➖ -1 глава", key=f"minus_{i}"):
                        if book["done_chapters"] > 0:
                            data["books"][i]["done_chapters"] -= 1
                            save_data(data)
                            st.rerun()
                with col_c:
                    if st.button("🗑 Удалить", key=f"del_{i}"):
                        data["books"].pop(i)
                        save_data(data)
                        st.rerun()

# ═══════════════════════════════════════
# РАЗДЕЛ 2: СЛОВА ЗА ДЕНЬ
# ═══════════════════════════════════════
elif menu == "📝 Слова за день":
    st.header("Слова за день")
    st.caption("Записывайте, сколько слов написали сегодня")

    today_str = str(date.today())
    today_words = data["daily_words"].get(today_str, 0)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Сегодня", f"{today_words} слов")
    with col2:
        total_words = sum(data["daily_words"].values())
        st.metric("Всего", f"{total_words} слов")

    st.divider()

    with st.form("add_words"):
        words = st.number_input("Сколько слов написали?", min_value=0, value=500, step=100)
        if st.form_submit_button("Записать"):
            data["daily_words"][today_str] = data["daily_words"].get(today_str, 0) + words
            save_data(data)
            st.success(f"Записано {words} слов. Всего за сегодня: {data['daily_words'][today_str]}")
            st.rerun()

    st.divider()
    st.subheader("История (последние 14 дней)")
    if data["daily_words"]:
        dates = sorted(data["daily_words"].keys())[-14:]
        df = pd.DataFrame({"Дата": dates, "Слова": [data["daily_words"][d] for d in dates]})
        st.bar_chart(df.set_index("Дата"))
    else:
        st.info("Пока нет записей.")

# ═══════════════════════════════════════
# РАЗДЕЛ 3: ЗАМЕТКИ
# ═══════════════════════════════════════
elif menu == "💡 Заметки":
    st.header("Идеи и заметки")

    with st.form("add_note"):
        note_title = st.text_input("Заголовок идеи")
        note_text = st.text_area("Описание", height=100)
        if st.form_submit_button("Сохранить заметку"):
            if note_title:
                data["notes"].append({
                    "title": note_title,
                    "text": note_text,
                    "date": str(date.today())
                })
                save_data(data)
                st.success("Заметка сохранена!")
                st.rerun()

    st.divider()
    if not data["notes"]:
        st.info("Пока нет заметок.")
    else:
        for i, note in enumerate(reversed(data["notes"])):
            with st.container(border=True):
                st.subheader(note["title"])
                st.caption(note["date"])
                if note["text"]:
                    st.write(note["text"])
                if st.button("🗑 Удалить", key=f"del_note_{i}"):
                    data["notes"].pop(len(data["notes"]) - 1 - i)
                    save_data(data)
                    st.rerun()

# ═══════════════════════════════════════
# РАЗДЕЛ 4: СТАТИСТИКА
# ═══════════════════════════════════════
elif menu == "📊 Статистика":
    st.header("Статистика")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Книг", len(data["books"]))
    with col2:
        total_done = sum(b["done_chapters"] for b in data["books"])
        total_plan = sum(b["total_chapters"] for b in data["books"])
        st.metric("Глав готово", f"{total_done} / {total_plan}")
    with col3:
        total_words = sum(data["daily_words"].values())
        st.metric("Слов всего", total_words)

    st.divider()

    if data["daily_words"]:
        st.subheader("Динамика слов (все время)")
        dates = sorted(data["daily_words"].keys())
        df = pd.DataFrame({"Дата": dates, "Слова": [data["daily_words"][d] for d in dates]})
        st.line_chart(df.set_index("Дата"))

        avg = total_words / len(dates) if dates else 0
        st.metric("Среднее в день", f"{avg:.0f} слов")
    else:
        st.info("Нет данных о словах.")

# ═══════════════════════════════════════
# РАЗДЕЛ 5: ПЕРСОНАЖИ
# ═══════════════════════════════════════
elif menu == "👥 Персонажи":
    st.header("👥 Персонажи")
    st.caption("Карточки героев и связи между ними")

    if "characters" not in data:
        data["characters"] = []
    if "relations" not in data:
        data["relations"] = []

    with st.expander("➕ Добавить персонажа"):
        with st.form("add_character"):
            name = st.text_input("Имя персонажа")
            role = st.selectbox("Роль", ["Главный герой", "Антагонист", "Второстепенный", "Эпизодический"])
            age = st.text_input("Возраст / возрастная группа")
            appearance = st.text_area("Внешность", height=80)
            character = st.text_area("Характер", height=80)
            goal = st.text_area("Цель / мотивация", height=80)
            conflict = st.text_area("Внутренний конфликт", height=80)
            submitted = st.form_submit_button("Добавить персонажа")
            if submitted and name:
                data["characters"].append({
                    "name": name, "role": role, "age": age,
                    "appearance": appearance, "character": character,
                    "goal": goal, "conflict": conflict,
                    "created": str(date.today())
                })
                save_data(data)
                st.success(f"Персонаж «{name}» добавлен!")
                st.rerun()

    if len(data["characters"]) >= 2:
        with st.expander("🔗 Добавить связь между персонажами"):
            with st.form("add_relation"):
                names = [c["name"] for c in data["characters"]]
                p1 = st.selectbox("Первый персонаж", names, key="rel_p1")
                p2 = st.selectbox("Второй персонаж", names, key="rel_p2")
                rel_type = st.selectbox("Тип связи", [
                    "Друзья", "Враги", "Любовь", "Семья", "Наставник / ученик",
                    "Соперники", "Союзники", "Предательство", "Тайная связь"
                ])
                rel_desc = st.text_input("Комментарий (необязательно)")
                if st.form_submit_button("Добавить связь"):
                    if p1 == p2:
                        st.error("Нельзя связать персонажа с самим собой.")
                    else:
                        data["relations"].append({
                            "p1": p1, "p2": p2, "type": rel_type,
                            "desc": rel_desc, "date": str(date.today())
                        })
                        save_data(data)
                        st.success(f"Связь «{p1} — {p2}» добавлена!")
                        st.rerun()

    if data["relations"]:
        st.subheader("🔗 Связи")
        for i, rel in enumerate(data["relations"]):
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f"**{rel['p1']}** ↔ **{rel['p2']}** — *{rel['type']}*")
                    if rel["desc"]:
                        st.caption(rel["desc"])
                with c2:
                    if st.button("🗑", key=f"del_rel_{i}"):
                        data["relations"].pop(i)
                        save_data(data)
                        st.rerun()

    st.divider()

    if not data["characters"]:
        st.info("Пока нет персонажей. Добавьте первого через кнопку выше.")
    else:
        roles = sorted(set(c["role"] for c in data["characters"]))
        selected_roles = st.multiselect("Фильтр по роли", roles, default=roles)
        filtered = [c for c in data["characters"] if c["role"] in selected_roles]

        for char in filtered:
            real_idx = data["characters"].index(char)
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(f"{char['name']} — {char['role']}")
                    if char["age"]:
                        st.caption(f"Возраст: {char['age']}")
                with col2:
                    if st.button("🗑 Удалить", key=f"del_char_{real_idx}"):
                        data["characters"].pop(real_idx)
                        data["relations"] = [
                            r for r in data["relations"]
                            if r["p1"] != char["name"] and r["p2"] != char["name"]
                        ]
                        save_data(data)
                        st.rerun()

                if char["appearance"]:
                    st.markdown(f"**Внешность:** {char['appearance']}")
                if char["character"]:
                    st.markdown(f"**Характер:** {char['character']}")
                if char["goal"]:
                    st.markdown(f"**Цель:** {char['goal']}")
                if char["conflict"]:
                    st.markdown(f"**Внутренний конфликт:** {char['conflict']}")

                char_rels = [r for r in data["relations"] if r["p1"] == char["name"] or r["p2"] == char["name"]]
                if char_rels:
                    st.markdown("**Связи:**")
                    for r in char_rels:
                        other = r["p2"] if r["p1"] == char["name"] else r["p1"]
                        st.markdown(f"- {other} — *{r['type']}*")

# ═══════════════════════════════════════
# РАЗДЕЛ 6: ДОСКА
# ═══════════════════════════════════════
elif menu == "🗂 Доска":
    st.header("🗂 Доска глав и сцен")
    st.caption("Канбан: Идея → В работе → Готово. Цвет карточки = книга.")

    if "board" not in data:
        data["board"] = {"ideas": [], "in_progress": [], "done": []}

    book_titles = [b["title"] for b in data.get("books", [])]

    COLOR_PALETTE = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
        "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
        "#F0B27A", "#82E0AA", "#F1948A", "#AED6F1", "#D7BDE2"
    ]

    book_colors = {}
    for idx, title in enumerate(book_titles):
        book_colors[title] = COLOR_PALETTE[idx % len(COLOR_PALETTE)]

    if book_titles:
        filter_book = st.selectbox("Показать карточки книги", ["Все книги"] + book_titles)
    else:
        filter_book = "Все книги"
        st.caption("Книг пока нет — карточки будут без привязки.")

    if book_titles:
        st.markdown("**Цвета книг:**")
        legend_cols = st.columns(min(len(book_titles), 4))
        for idx, title in enumerate(book_titles):
            with legend_cols[idx % 4]:
                st.markdown(
                    f'<span style="background-color:{book_colors[title]}; '
                    f'padding:2px 8px; border-radius:4px; color:#000; font-size:12px;">'
                    f'{title}</span>',
                    unsafe_allow_html=True
                )

    with st.expander("➕ Добавить карточку"):
        with st.form("add_card"):
            card_title = st.text_input("Название главы / сцены")
            card_desc = st.text_area("Краткое описание", height=80)
            card_book = st.selectbox("Привязать к книге", ["Без привязки"] + book_titles)
            column = st.selectbox("Колонка", ["ideas", "in_progress", "done"],
                                  format_func=lambda x: {"ideas": "💡 Идея", "in_progress": "✍️ В работе", "done": "✅ Готово"}[x])
            if st.form_submit_button("Добавить карточку"):
                if card_title:
                    data["board"][column].append({
                        "title": card_title, "desc": card_desc,
                        "book": None if card_book == "Без привязки" else card_book,
                        "date": str(date.today())
                    })
                    save_data(data)
                    st.success("Карточка добавлена!")
                    st.rerun()

    st.divider()

    def match_filter(card):
        if filter_book == "Все книги":
            return True
        return card.get("book") == filter_book

    def card_color(card):
        if card.get("book") and card["book"] in book_colors:
            return book_colors[card["book"]]
        return "#E0E0E0"

    def render_card(card):
        color = card_color(card)
        book_label = card.get("book") or "Без книги"
        st.markdown(
            f'<div style="border-left: 6px solid {color}; padding-left: 10px; '
            f'margin-bottom: 5px;">'
            f'<b>{card["title"]}</b><br>'
            f'<span style="font-size:12px; color:#666;">📚 {book_label}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        if card["desc"]:
            st.caption(card["desc"])
        st.caption(card["date"])

    col_idea, col_work, col_done = st.columns(3)

    with col_idea:
        st.subheader("💡 Идея")
        cards = [(i, c) for i, c in enumerate(data["board"]["ideas"]) if match_filter(c)]
        if not cards:
            st.caption("Пусто")
        for i, card in cards:
            with st.container(border=True):
                render_card(card)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("➡️ В работу", key=f"idea_to_work_{i}"):
                        data["board"]["in_progress"].append(data["board"]["ideas"].pop(i))
                        save_data(data)
                        st.rerun()
                with c2:
                    if st.button("🗑", key=f"del_idea_{i}"):
                        data["board"]["ideas"].pop(i)
                        save_data(data)
                        st.rerun()

    with col_work:
        st.subheader("✍️ В работе")
        cards = [(i, c) for i, c in enumerate(data["board"]["in_progress"]) if match_filter(c)]
        if not cards:
            st.caption("Пусто")
        for i, card in cards:
            with st.container(border=True):
                render_card(card)
                c1, c2, c3 = st.columns(3)
                with c1:
                    if st.button("⬅️", key=f"work_back_{i}"):
                        data["board"]["ideas"].append(data["board"]["in_progress"].pop(i))
                        save_data(data)
                        st.rerun()
                with c2:
                    if st.button("✅", key=f"work_done_{i}"):
                        data["board"]["done"].append(data["board"]["in_progress"].pop(i))
                        save_data(data)
                        st.rerun()
                with c3:
                    if st.button("🗑", key=f"del_work_{i}"):
                        data["board"]["in_progress"].pop(i)
                        save_data(data)
                        st.rerun()

    with col_done:
        st.subheader("✅ Готово")
        cards = [(i, c) for i, c in enumerate(data["board"]["done"]) if match_filter(c)]
        if not cards:
            st.caption("Пусто")
        for i, card in cards:
            with st.container(border=True):
                render_card(card)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("⬅️ Назад", key=f"done_back_{i}"):
                        data["board"]["in_progress"].append(data["board"]["done"].pop(i))
                        save_data(data)
                        st.rerun()
                with c2:
                    if st.button("🗑", key=f"del_done_{i}"):
                        data["board"]["done"].pop(i)
                        save_data(data)
                        st.rerun()

    st.divider()
    total = len(data["board"]["ideas"]) + len(data["board"]["in_progress"]) + len(data["board"]["done"])
    st.caption(f"Всего карточек: {total}")

# ═══════════════════════════════════════
# РАЗДЕЛ 7: НОВОСТИ ИИ
# ═══════════════════════════════════════
elif menu == "📰 Новости ИИ":
    st.header("📰 Новости по нейросетям")
    st.caption("Свежие материалы из RSS-лент. Кэш обновляется каждые 10 минут.")

    RSS_FEEDS = {
        "OpenAI Blog": "https://openai.com/blog/rss.xml",
        "Hugging Face": "https://huggingface.co/blog/feed.xml",
        "Google DeepMind": "https://deepmind.google/blog/rss.xml",
        "The Batch (DeepLearning.AI)": "https://www.deeplearning.ai/the-batch/feed/",
        "MIT Tech Review AI": "https://www.technologyreview.com/topic/artificial-intelligence/feed",
    }

    @st.cache_data(ttl=600)
    def fetch_rss(url):
        articles = []
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                root = ET.fromstring(resp.read())
            for item in root.findall(".//item")[:15]:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                pub_date = (item.findtext("pubDate") or "").strip()
                desc = (item.findtext("description") or "").strip()
                if desc:
                    desc = desc[:180] + "..." if len(desc) > 180 else desc
                articles.append({
                    "title": title, "link": link, "date": pub_date,
                    "description": desc, "source": None
                })
        except Exception as e:
            st.warning(f"Не удалось загрузить {url}: {e}")
        return articles

    all_news = []
    for source_name, feed_url in RSS_FEEDS.items():
        items = fetch_rss(feed_url)
        for item in items:
            item["source"] = source_name
        all_news.extend(items)

    st.sidebar.subheader("Фильтры новостей")
    sources = sorted(set(n["source"] for n in all_news))
    selected_sources = st.sidebar.multiselect("Источники", sources, default=sources)
    search_query = st.sidebar.text_input("Поиск по заголовку", "")

    filtered_news = [
        n for n in all_news
        if n["source"] in selected_sources
        and (search_query.lower() in n["title"].lower() if search_query else True)
    ]

    st.caption(f"Всего новостей: {len(filtered_news)} (из {len(all_news)} загруженных)")

    if not filtered_news:
        st.info("Новостей не найдено. Попробуйте изменить фильтры.")
    else:
        for news in filtered_news:
            with st.container():
                st.subheader(news["title"])
                col1, col2 = st.columns([3, 1])
                with col1:
                    if news["description"]:
                        st.write(news["description"])
                with col2:
                    st.caption(f"**{news['source']}**")
                    if news["date"]:
                        st.caption(news["date"][:16])
                if news["link"]:
                    st.markdown(f"[Читать →]({news['link']})")
                st.divider()