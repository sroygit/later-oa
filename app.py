"""Betty's UI. Run:  .venv/bin/streamlit run app.py"""
from __future__ import annotations

from datetime import date

import streamlit as st

from projects_client import STATUSES, ApiError, Projects, from_ms

st.set_page_config(page_title="Projects", layout="wide")
api = Projects()


@st.cache_data(ttl=5)
def load():
    return api.list_projects()


def fmt(ms):
    d = from_ms(ms)
    return d.date().isoformat() if d else "—"


projects = load()
tab_proj, tab_port = st.tabs(["Projects", "Portfolio"])

with tab_proj:
    left, right = st.columns([1, 3])
    with left:
        titles = [p["title"] for p in projects]
        pick = st.selectbox("Project", titles) if titles else None
        with st.expander("New project"):
            with st.form("new"):
                t = st.text_input("Title")
                d = st.text_area("Description")
                s = st.selectbox("Status", STATUSES)
                if st.form_submit_button("Create") and t:
                    api.create(t, d, s); load.clear(); st.rerun()
    with right:
        if pick:
            p = next(x for x in projects if x["title"] == pick)
            st.subheader(p["title"])
            st.caption(f"{p['id']} · updated {fmt(p['updated_at'])}")
            c1, c2 = st.columns([3, 1])
            new_status = c1.selectbox("Status", STATUSES, index=STATUSES.index(p["status"]) if p["status"] in STATUSES else 0)
            if c2.button("Save status") and new_status != p["status"]:
                try:
                    api.modify(p["id"], status=new_status); load.clear(); st.rerun()
                except ApiError as e:
                    st.error(str(e))
            if p.get("description"):
                st.write(p["description"])

            st.markdown("**Todos**")
            for t in p.get("items") or []:
                a, b, c, dcol = st.columns([0.5, 4, 2, 0.7])
                done = a.checkbox("", value=bool(t["done"]), key=f"d-{t['id']}", label_visibility="collapsed")
                if done != bool(t["done"]):
                    api.mark(p["id"], t["id"], done); load.clear(); st.rerun()
                b.write(("~~" + t["task"] + "~~") if t["done"] else t["task"])
                c.caption(f"{t.get('who') or 'unassigned'} · due {fmt(t.get('by'))}")
                if dcol.button("🗑", key=f"y-{t['id']}"):
                    api.yank(p["id"], t["id"]); load.clear(); st.rerun()

            with st.form("add", clear_on_submit=True):
                f1, f2, f3, f4 = st.columns([4, 2, 2, 1])
                task = f1.text_input("Task")
                who = f2.text_input("Who")
                due = f3.date_input("Due", value=None)
                if f4.form_submit_button("Add") and task:
                    api.add_item(p["id"], task, who=who, by=due); load.clear(); st.rerun()

with tab_port:
    rows = api.summary()
    st.dataframe(
        [{"Project": r["title"], "Status": r["status"], "Open": r["open"], "Done": r["done"],
          "Overdue": r["overdue"], "Updated": r["updated_at"].date().isoformat() if r["updated_at"] else "—",
          "Changed this week": "✓" if r["changed_this_week"] else "", "Stuck": "⚠️" if r["stuck"] else ""}
         for r in rows],
        use_container_width=True, hide_index=True)
    late = api.overdue()
    st.markdown(f"**Overdue todos ({len(late)})**")
    for t in late:
        st.write(f"- {t['task']} — {t.get('who') or 'unassigned'}, due {fmt(t['by'])} · *{t['project_title']}*")
