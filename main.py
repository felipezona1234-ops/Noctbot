import discord
from discord.ext import commands
import os
import time
import random
from datetime import timedelta
from collections import defaultdict
from flask import Flask
from threading import Thread

# Para que Render no lo apague - 24/7
app = Flask('')
@app.route('/')
def home():
    return "NOCTBOT esta vivo"
def run():
    app.run(host='0.0.0.0', port=8080)
Thread(target=run).start()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# CONFIGURACION
antiraid_activo = True
antilink_activo = True
whitelist_usuarios = set()
joins_recientes = []
mensajes_usuario = defaultdict(list)
warns = defaultdict(list)

LINKS_PROHIBIDOS = ["discord.gg", "discord.com/invite", "discordapp.com/invite", "t.me/", "bit.ly", "tinyurl", "grabify", "http://", "https://", "www."]

FRASES_DESCANSAR = [
    "Deja descansar 😴",
    "Deja descansar bro, estoy chambiando",
    "Deja descansar, ando vigilando el server 🛡️",
    "Deja descansar 😴 ¿Qué quieres?",
    "Ay, deja descansar... ¿Qué pasó?",
]

@bot.event
async def on_ready():
    print(f"NOCTBOT conectado como {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Sincronizados {len(synced)} comandos")
    except Exception as e:
        print(e)

@bot.event
async def on_member_join(member):
    if not antiraid_activo:
        return
    ahora = time.time()
    joins_recientes.append(ahora)
    while joins_recientes and joins_recientes[0] < ahora - 10:
        joins_recientes.pop(0)
    if len(joins_recientes) >= 5:
        for canal in member.guild.text_channels:
            if "log" in canal.name or "mod" in canal.name or "general" in canal.name:
                try:
                    await canal.send(f"🚨 **POSIBLE RAID DETECTADO** - Entraron {len(joins_recientes)} usuarios en 10 segundos. Revisen!")
                    break
                except: pass
        joins_recientes.clear()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if not message.guild:
        return

    contenido_lower = message.content.lower()
    fue_mencionado = bot.user in message.mentions
    lo_nombraron = "noctbot" in contenido_lower or "noct bot" in contenido_lower
    if fue_mencionado or lo_nombraron:
        await message.reply(random.choice(FRASES_DESCANSAR))
        return

    if antilink_activo and message.author.id not in whitelist_usuarios:
        if not message.author.guild_permissions.administrator:
            for link in LINKS_PROHIBIDOS:
                if link in contenido_lower:
                    try:
                        await message.delete()
                        await message.channel.send(f"{message.author.mention} ❌ No puedes enviar links en este servidor.", delete_after=5)
                    except: pass
                    return

    if antiraid_activo and not message.author.guild_permissions.administrator:
        ahora = time.time()
        mensajes_usuario[message.author.id].append(ahora)
        mensajes_usuario[message.author.id] = [t for t in mensajes_usuario[message.author.id] if t > ahora - 5]
        if len(mensajes_usuario[message.author.id]) >= 5:
            try:
                await message.channel.send(f"{message.author.mention} ⏳ Estás enviando mensajes muy rápido, tranquilo.", delete_after=5)
                mensajes_usuario[message.author.id].clear()
            except: pass

    await bot.process_commands(message)

@bot.tree.command(name="antiraid", description="Prender o apagar anti-raid")
async def antiraid(interaction: discord.Interaction, estado: str):
    global antiraid_activo
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permiso.", ephemeral=True); return
    antiraid_activo = estado.lower() == "on"
    await interaction.response.send_message(f"Anti-Raid: {'🟢 ACTIVADO' if antiraid_activo else '🔴 DESACTIVADO'}")

@bot.tree.command(name="antilink", description="Prender o apagar anti-links")
async def antilink(interaction: discord.Interaction, estado: str):
    global antilink_activo
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permiso.", ephemeral=True); return
    antilink_activo = estado.lower() == "on"
    await interaction.response.send_message(f"Anti-Link: {'🟢 ACTIVADO' if antilink_activo else '🔴 DESACTIVADO'}")

@bot.tree.command(name="whitelist", description="Permitir que un usuario mande links")
async def whitelist(interaction: discord.Interaction, usuario: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("No tienes permiso.", ephemeral=True); return
    whitelist_usuarios.add(usuario.id)
    await interaction.response.send_message(f"✅ {usuario.mention} ya puede enviar links.")

@bot.tree.command(name="ban", description="Banear a un usuario")
async def ban(interaction: discord.Interaction, usuario: discord.Member, razon: str = "Sin razón"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ No tienes permiso.", ephemeral=True); return
    try:
        await usuario.ban(reason=razon)
        await interaction.response.send_message(f"🔨 {usuario.mention} fue baneado. Razón: {razon}")
    except Exception as e:
        await interaction.response.send_message(f"No pude banearlo. Error: {e}", ephemeral=True)

@bot.tree.command(name="unban", description="Desbanear a un usuario")
async def unban(interaction: discord.Interaction, usuario_id: str, razon: str = "Sin razón"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("❌ No tienes permiso.", ephemeral=True); return
    try:
        usuario = await bot.fetch_user(int(usuario_id))
        await interaction.guild.unban(usuario, reason=razon)
        await interaction.response.send_message(f"✅ {usuario.mention} fue desbaneado.")
    except Exception as e:
        await interaction.response.send_message(f"No pude desbanearlo. Error: {e}", ephemeral=True)

@bot.tree.command(name="kick", description="Expulsar a un usuario")
async def kick(interaction: discord.Interaction, usuario: discord.Member, razon: str = "Sin razón"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("❌ No tienes permiso.", ephemeral=True); return
    try:
        await usuario.kick(reason=razon)
        await interaction.response.send_message(f"👢 {usuario.mention} fue expulsado. Razón: {razon}")
    except Exception as e:
        await interaction.response.send_message(f"No pude expulsarlo. Error: {e}", ephemeral=True)

@bot.tree.command(name="warn", description="Dar una advertencia")
async def warn(interaction: discord.Interaction, usuario: discord.Member, razon: str = "Sin razón"):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ No tienes permiso.", ephemeral=True); return
    warns[usuario.id].append(razon)
    cantidad = len(warns[usuario.id])
    await interaction.response.send_message(f"⚠️ {usuario.mention} recibió warn. Razón: {razon}\nAhora tiene **{cantidad}** warn(s).")
    if cantidad >= 3:
        try:
            await usuario.ban(reason="3 warns acumulados")
            await interaction.channel.send(f"🔨 {usuario.mention} fue baneado por 3 warns.")
        except: pass

@bot.tree.command(name="warns", description="Ver warns de un usuario")
async def warns_cmd(interaction: discord.Interaction, usuario: discord.Member):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("No tienes permiso.", ephemeral=True); return
    lista = warns.get(usuario.id, [])
    if not lista:
        await interaction.response.send_message(f"{usuario.mention} no tiene warns. ✅")
    else:
        texto = "\n".join([f"{i+1}. {r}" for i, r in enumerate(lista)])
        await interaction.response.send_message(f"⚠️ **Warns de {usuario.mention} ({len(lista)}):**\n{texto}")

@bot.tree.command(name="lock", description="Bloquear el canal actual")
async def lock(interaction: discord.Interaction, razon: str = "Canal bloqueado"):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ No tienes permiso.", ephemeral=True); return
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
    await interaction.response.send_message(f"🔒 Canal bloqueado. Razón: {razon}")

@bot.tree.command(name="unlock", description="Desbloquear el canal actual")
async def unlock(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_channels:
        await interaction.response.send_message("❌ No tienes permiso.", ephemeral=True); return
    await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
    await interaction.response.send_message(f"🔓 Canal desbloqueado.")

@bot.tree.command(name="purge", description="Borrar mensajes del canal")
async def purge(interaction: discord.Interaction, cantidad: int):
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ No tienes permiso.", ephemeral=True); return
    if cantidad < 1 or cantidad > 100:
        await interaction.response.send_message("Pon un número entre 1 y 100.", ephemeral=True); return
    await interaction.response.defer(ephemeral=True)
    borrados = await interaction.channel.purge(limit=cantidad)
    await interaction.followup.send(f"🧹 Se borraron **{len(borrados)}** mensajes.", ephemeral=True)

@bot.tree.command(name="mute", description="Mutear a un usuario por minutos")
async def mute(interaction: discord.Interaction, usuario: discord.Member, minutos: int = 10, razon: str = "Sin razón"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ No tienes permiso.", ephemeral=True); return
    try:
        await usuario.timeout(timedelta(minutes=minutos), reason=razon)
        await interaction.response.send_message(f"🔇 {usuario.mention} fue muteado por **{minutos} minutos**. Razón: {razon}")
    except Exception as e:
        await interaction.response.send_message(f"No pude mutearlo. Error: {e}", ephemeral=True)

@bot.tree.command(name="unmute", description="Quitar el mute")
async def unmute(interaction: discord.Interaction, usuario: discord.Member):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("❌ No tienes permiso.", ephemeral=True); return
    try:
        await usuario.timeout(None)
        await interaction.response.send_message(f"🔊 {usuario.mention} ya puede hablar.")
    except Exception as e:
        await interaction.response.send_message(f"No pude desmutearlo. Error: {e}", ephemeral=True)

bot.run(os.getenv("TOKEN"))
