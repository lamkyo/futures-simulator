#!/usr/bin/env python3
"""
Tier 3: AI Reviewer Agent
Parses reports/tier2/summary.json, generates expert quantitative assessment,
and sends concise Telegram brief if configured.
"""
import json
import os
import sys
from pathlib import Path
import requests

def generate_local_review(summary: dict) -> str:
    verdict = summary.get("overall_verdict", "UNKNOWN")
    dsr_info = summary.get("checks", {}).get("dsr", {})
    dsr_val = dsr_info.get("value", "N/A")
    failed_gates = summary.get("failed_gates", [])

    if verdict == "PASS":
        status_line = "🟢 <b>VERDICT: PASS — ĐỦ ĐIỀU KIỆN ĐI TIẾP</b>"
        explanation = "Chiến lược vượt qua bài kiểm tra Deflated Sharpe Ratio và các tiêu chí biến thiên tham số. Đủ điều kiện chuyển sang giai đoạn paper-trade."
        action = "👉 <b>Hành động tiếp theo:</b> Triển khai paper-trading 4 tuần với vốn ảo để kiểm tra slippage thực tế."
    else:
        status_line = "🔴 <b>VERDICT: FAIL — BỊ LOẠI Ở TIER 2</b>"
        explanation = f"Chiến lược không vượt qua kiểm định thống kê DSR (DSR: {dsr_val} < 0.95). Lợi nhuận quan sát được nhiều khả năng là do Data Snooping / Multiple Testing sau 36 trials."
        action = "👉 <b>Hành động tiếp theo:</b> Dừng chiến lược này, TUYỆT ĐỐI KHÔNG TUNE THÊM THAM SỐ. Đưa vào Kill List trung thực và chuyển nguồn lực sang phát triển pipeline cho Upwork."

    failed_str = "\n".join([f"  • {f}" for f in failed_gates]) if failed_gates else "  • Không có vi phạm."

    report = (
        f"🤖 <b>[AI QUANT REVIEWER] BÁO CÁO ĐÁNH GIÁ TIER 2</b>\n\n"
        f"{status_line}\n\n"
        f"<b>1. Nhận định cốt lõi:</b>\n{explanation}\n\n"
        f"<b>2. Cổng kiểm định không đạt:</b>\n{failed_str}\n\n"
        f"{action}"
    )
    return report

def main():
    summary_path = Path("reports/tier2/summary.json")
    if not summary_path.exists():
        print(f"File {summary_path} không tồn tại. Bỏ qua review.")
        sys.exit(0)

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    # 1. Sinh bản đánh giá định lượng
    ai_report_text = generate_local_review(summary)

    # Lưu ra file markdown
    out_md = Path("reports/tier2/ai_verdict.md")
    out_md.write_text(ai_report_text.replace("<b>", "**").replace("</b>", "**"), encoding="utf-8")
    print(f"AI Reviewer đã xuất bản đánh giá tại: {out_md}")
    print("\n" + ai_report_text + "\n")

    # 2. Gửi Telegram nếu có token
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat = os.environ.get("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat:
        try:
            resp = requests.post(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                json={
                    "chat_id": tg_chat,
                    "text": ai_report_text,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            if resp.status_code == 200:
                print("-> Đã gửi báo cáo AI Reviewer qua Telegram thành công!")
        except Exception as e:
            print(f"Warning: không thể gửi alert Telegram: {e}")

if __name__ == "__main__":
    main()
