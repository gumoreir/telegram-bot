import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIG
# =========================
TOKEN = "8360307041:AAEkyfJGxeVD4ZIV_qRXrR-A4cPuO3CwDPE"
ADMIN_ID = 5104231957

LINK_FERRAMENTA = "https://t.me/TEU_LINK_DA_FERRAMENTA"
LINK_GRUPO_PRIVADO = "https://t.me/TEU_GRUPO_PRIVADO"

PARCERIAS = {
    "Lollyspins": "https://partners.meratrack.xyz/click?o=384&a=1049",
    "Casabet":    "https://partners.meratrack.xyz/click?o=382&a=1049",
    "SLOTT":      "https://partners.meratrack.xyz/click?o=373&a=1049",
    "LEONBET":    "https://partners.meratrack.xyz/click?o=383&a=1049",
}

HELP_HINT = "\n\n🆘 Se precisares de ajuda, escreve /help"


# =========================
# HELPERS
# =========================
def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Ferramenta BacBo (AI)", callback_data="interest_BACBO")],
        [InlineKeyboardButton("💰 Só Devolução do Depósito", callback_data="interest_DEVOLUCAO")],
        [InlineKeyboardButton("🔥 Ambos (Ferramenta + Devolução)", callback_data="interest_AMBOS")],
    ])

def parcerias_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for nome, url in PARCERIAS.items():
        rows.append([InlineKeyboardButton(f"🎰 {nome}", url=url)])
    rows.append([InlineKeyboardButton("✅ Já criei conta e depositei", callback_data="deposited_ready")])
    return InlineKeyboardMarkup(rows)

def payout_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💸 MBWay", callback_data="payout_MBWAY")],
        [InlineKeyboardButton("🪙 Crypto (USDC)", callback_data="payout_USDC")],
    ])

def admin_decision_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Aprovar", callback_data=f"admin_approve_{user_id}"),
        InlineKeyboardButton("❌ Rejeitar", callback_data=f"admin_reject_{user_id}"),
    ]])

def format_user_header(u) -> str:
    return (
        f"👤 *Nome:* {u.full_name}\n"
        f"🔎 *Username:* @{u.username if u.username else '—'}\n"
        f"🆔 *ID:* `{u.id}`\n"
    )

def user_summary(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    u = update.effective_user
    interest = context.user_data.get("interest", "-")
    payout_method = context.user_data.get("payout_method", "-")
    payout_value = context.user_data.get("payout_value", "-")

    return (
        "📩 *NOVO PEDIDO*\n\n"
        + format_user_header(u) +
        f"\n📌 *Interesse:* {interest}\n"
        f"💳 *Pagamento:* {payout_method}\n"
        f"📥 *Destino:* `{payout_value}`\n"
    )


# =========================
# START / FLOW
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    text = (
        "Hey! Tudo bem? 👋\n"
        "Provavelmente vieste do meu Instagram 😉\n\n"
        "Antes de avançarmos, diz-me o que procuras:\n"
        "• 🤖 Ferramenta BacBo (AI)\n"
        "• 💰 Só Devolução do Depósito\n"
        "• 🔥 Ambos (Ferramenta + Devolução)\n\n"
        "Escolhe uma opção abaixo:"
        + HELP_HINT
    )
    await update.message.reply_text(text, reply_markup=main_menu_keyboard())

async def choose_interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    interest = q.data.replace("interest_", "")
    context.user_data["interest"] = interest

    text = (
        "✅ *Perfeito!* Aqui vai o importante:\n\n"
        "⚠️ *A devolução é até 50€*\n"
        "✔️ Válido apenas para *contas novas*\n"
        "✔️ A devolução e/ou acesso à ferramenta só ficam disponíveis se te registares "
        "numa das minhas parcerias (pode ser qualquer uma)\n\n"
        "📌 *Como funciona:*\n"
        "1) Cria conta numa das plataformas abaixo\n"
        "2) Faz o depósito\n"
        "3) Envia-me o *print/comprovativo do depósito*\n\n"
        "Se já tiveres conta numa delas, escolhe outra."
        + HELP_HINT
    )
    await q.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=parcerias_keyboard())

async def deposited_ready(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    # ----- BUG FIX #1 -----
    # Se o utilizador carregou em "Já depositei" mas ainda não escolheu interesse,
    # define um valor por defeito para não ficar bloqueado.
    if not context.user_data.get("interest"):
        context.user_data["interest"] = "AMBOS"

    text = (
        "Boa! ✅\n\n"
        "Agora diz-me *como queres receber a devolução*:\n"
        "💸 MBWay (envias o teu número)\n"
        "🪙 Crypto (USDC) (envias a tua wallet)\n\n"
        "Escolhe uma opção:"
        + HELP_HINT
    )
    await q.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=payout_keyboard())

async def payout_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    method = q.data.replace("payout_", "")
    context.user_data["payout_method"] = method

    # ----- BUG FIX #2 -----
    # Limpa payout_value e awaiting_proof para garantir estado limpo
    context.user_data.pop("payout_value", None)
    context.user_data.pop("awaiting_proof", None)

    if method == "MBWAY":
        await q.edit_message_text(
            "📲 Perfeito! Envia agora o teu *número de telemóvel* (MBWay).\n\n"
            "Ex: 9XXXXXXXX"
            + HELP_HINT,
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await q.edit_message_text(
            "🪙 Perfeito! Envia agora a tua *wallet USDC*.\n\n"
            "⚠️ Confere bem antes de enviar."
            + HELP_HINT,
            parse_mode=ParseMode.MARKDOWN
        )


# =========================
# SUPORTE / HELP (TICKET)
# =========================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["support_mode"] = True
    await update.message.reply_text(
        "🆘 *Suporte ativado!*\n\n"
        "Escreve a tua dúvida aqui e eu encaminho para o suporte.\n"
        "Para sair do suporte: /cancel",
        parse_mode=ParseMode.MARKDOWN
    )

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["support_mode"] = False
    await update.message.reply_text(
        "✅ Ok! Saíste do suporte. Se precisares novamente escreve /help 🙂"
    )


# =========================
# SUPORTE: RESPOSTA DO ADMIN (BIDIRECIONAL)
# =========================
async def admin_reply_to_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Se o ADMIN responder (reply) a uma mensagem de suporte, reenvia para o utilizador.
    Este handler SÓ é chamado para mensagens do ADMIN.
    """
    msg = update.message
    if not msg or not msg.reply_to_message:
        # Admin enviou mensagem sem ser reply — ignora silenciosamente
        return

    support_map = context.application.bot_data.get("support_map", {})
    original_admin_message_id = msg.reply_to_message.message_id
    user_id = support_map.get(original_admin_message_id)

    if not user_id:
        # Não é uma mensagem de suporte rastreada — ignora
        return

    await context.bot.send_message(
        chat_id=user_id,
        text="🆘 *Suporte:* " + (msg.text or ""),
        parse_mode=ParseMode.MARKDOWN
    )
    await msg.reply_text("✅ Resposta enviada ao utilizador.")


# =========================
# TEXTO GERAL (UTILIZADORES)
# =========================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler de texto para utilizadores normais (não-admin).
    Ordem de prioridade:
    1) Modo suporte ativo → encaminha para admin
    2) À espera de payout_value → guarda número/wallet
    3) Caso contrário → mensagem genérica
    """
    text = (update.message.text or "").strip()
    user = update.effective_user

    # 1) MODO SUPORTE
    if context.user_data.get("support_mode"):
        sent = await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "🆘 *PEDIDO DE SUPORTE*\n\n"
                + format_user_header(user) +
                "\n💬 *Mensagem:*\n"
                f"{text}\n\n"
                "↩️ *Responde a ESTA mensagem* para o bot enviar a resposta ao utilizador."
            ),
            parse_mode=ParseMode.MARKDOWN
        )
        context.application.bot_data.setdefault("support_map", {})[sent.message_id] = user.id
        await update.message.reply_text(
            "✅ Mensagem enviada ao suporte.\n"
            "Assim que responder, vais receber aqui no bot."
        )
        return

    # 2) RECEBER DESTINO DO PAGAMENTO (MBWAY / USDC)
    # ----- BUG FIX #3 -----
    # Condição mais robusta: só entra aqui se tiver payout_method definido
    # e payout_value ainda não estiver definido
    if context.user_data.get("payout_method") and "payout_value" not in context.user_data:
        if len(text) < 5:
            await update.message.reply_text("Envia um valor válido, por favor 🙂" + HELP_HINT)
            return

        context.user_data["payout_value"] = text
        context.user_data["awaiting_proof"] = True

        await update.message.reply_text(
            "✅ Obrigado! Agora envia o *print/comprovativo do depósito* (foto ou PDF).\n\n"
            "Assim que estiver validado:\n"
            "✔️ Recebes acesso à ferramenta privada (se escolheste Ferramenta/ Ambos)\n"
            "✔️ Ficas a aguardar a devolução (normalmente 1–2 dias úteis)\n\n"
            "📎 Envia o comprovativo aqui:"
            + HELP_HINT,
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # 3) TEXTO FORA DE CONTEXTO
    await update.message.reply_text(
        "Para começar escreve /start 🙂"
        + HELP_HINT
    )


# =========================
# COMPROVATIVOS -> ADMIN
# =========================
async def receber_foto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ----- BUG FIX #4 -----
    # Se não está em awaiting_proof mas tem payout_value, ainda aceita
    # (protege contra estados inconsistentes)
    has_proof_state = (
        context.user_data.get("awaiting_proof") or
        context.user_data.get("payout_value")
    )

    if not has_proof_state:
        await update.message.reply_text("Para começar, escreve /start 🙂" + HELP_HINT)
        return

    user = update.effective_user
    photo = update.message.photo[-1]

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo.file_id,
        caption=user_summary(update, context),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=admin_decision_keyboard(user.id),
    )

    context.user_data["awaiting_proof"] = False  # evita reenvio duplo
    await update.message.reply_text("✅ Comprovativo recebido. Aguarda validação. 🙌" + HELP_HINT)

async def receber_documento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    has_proof_state = (
        context.user_data.get("awaiting_proof") or
        context.user_data.get("payout_value")
    )

    if not has_proof_state:
        await update.message.reply_text("Para começar, escreve /start 🙂" + HELP_HINT)
        return

    user = update.effective_user
    doc = update.message.document

    await context.bot.send_document(
        chat_id=ADMIN_ID,
        document=doc.file_id,
        caption=user_summary(update, context),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=admin_decision_keyboard(user.id),
    )

    context.user_data["awaiting_proof"] = False
    await update.message.reply_text("✅ Documento recebido. Aguarda validação. 🙌" + HELP_HINT)


# =========================
# ADMIN: APROVAR / REJEITAR
# =========================
async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.from_user.id != ADMIN_ID:
        await q.edit_message_text("Sem permissões.")
        return

    parts = q.data.split("_")
    action = parts[1]
    user_id = int(parts[2])

    if action == "approve":
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "✅ *APROVADO!*\n\n"
                "🔐 *Acesso à ferramenta privada:*\n"
                f"{LINK_FERRAMENTA}\n\n"
                "👥 *Grupo/Canal privado:*\n"
                f"{LINK_GRUPO_PRIVADO}\n\n"
                "💰 A devolução (até 50€) fica em processamento e normalmente é feita em *1–2 dias úteis*.\n"
                "Se precisares de ajuda escreve /help"
            ),
            parse_mode=ParseMode.MARKDOWN
        )
        await q.edit_message_text("✅ Utilizador APROVADO e notificado.")

    elif action == "reject":
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "❌ *O comprovativo foi rejeitado.*\n\n"
                "Possíveis motivos:\n"
                "• Não é conta nova\n"
                "• Depósito não aparece/ilegível\n"
                "• Link/parceria não foi usada\n\n"
                "Se achas que foi erro, envia novo comprovativo ou escreve /help"
            ),
            parse_mode=ParseMode.MARKDOWN
        )
        await q.edit_message_text("❌ Utilizador REJEITADO e notificado.")


# =========================
# MAIN
# =========================
def main():
    if not TOKEN:
        raise RuntimeError("Define a variável de ambiente BOT_TOKEN com o token do teu bot.")

    app = Application.builder().token(TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("cancel", cancel_command))

    # Callbacks de botões inline
    app.add_handler(CallbackQueryHandler(choose_interest,  pattern=r"^interest_(BACBO|AMBOS|DEVOLUCAO)$"))
    app.add_handler(CallbackQueryHandler(deposited_ready,  pattern=r"^deposited_ready$"))
    app.add_handler(CallbackQueryHandler(payout_choice,    pattern=r"^payout_(MBWAY|USDC)$"))
    app.add_handler(CallbackQueryHandler(admin_decision,   pattern=r"^admin_(approve|reject)_\d+$"))

    # ----- BUG FIX #5 (PRINCIPAL) -----
    # O handler do ADMIN deve filtrar apenas replies para não engolir texto normal do admin.
    # Usando filters.REPLY garante que só interceta mensagens de resposta (reply),
    # deixando o handle_text tratar os restantes casos do admin normalmente.
    app.add_handler(MessageHandler(
        filters.TEXT & filters.User(ADMIN_ID) & filters.REPLY,
        admin_reply_to_support
    ))

    # Comprovativos (foto e documento)
    app.add_handler(MessageHandler(filters.PHOTO, receber_foto))
    app.add_handler(MessageHandler(filters.Document.ALL, receber_documento))

    # Texto geral — utilizadores normais E admin sem reply
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 Bot a correr...")
    app.run_polling()

if __name__ == "__main__":
    main()