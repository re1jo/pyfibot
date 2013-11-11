# -*- coding: utf-8 -*-
import sys
import pygeoip
import os.path
import socket
import sqlite3
import time

DATAFILE = os.path.join(sys.path[0], "GeoIP.dat")
# STANDARD = reload from disk
# MEMORY_CACHE = load to memory
# MMAP_CACHE = memory using mmap
gi4 = pygeoip.GeoIP(DATAFILE, pygeoip.MEMORY_CACHE)


def init(botconfig):
  open_DB(True)


def open_DB(createTable=False, db="module_geokick.db"):
  conn = sqlite3.connect(db)
  c = conn.cursor()
  if createTable:
    c.execute('CREATE TABLE IF NOT EXISTS exceptions (hostmask);')
    conn.commit()
  return conn, c


def command_geo_exempt(bot, user, channel, args):
  """.geo_add nick!ident@hostname"""
  if get_op_status(user):
    if not get_exempt_status(args):
      conn, c = open_DB()
      insert = "INSERT INTO exceptions VALUES ('" + args + "');"
      c.execute(insert)
      conn.commit()
      conn.close()
      bot.say(channel, "Poikkeus lisätty.")
      return True
    else:
      return bot.say(channel, "Virhe: Poikkeus on jo listalla!")


def command_geo_list(bot, user, channel, args):
  if get_op_status(user):
    conn, c = open_DB()
    c.execute('SELECT hostmask FROM exceptions;')
    rows = c.fetchall()
    conn.close()
    if rows:
      excepts = str("")
      j   = 0
      for i in rows:
        excepts += "[" + i[0] + "] "
      return bot.say(channel, "Poikkeukset: " + excepts)
    else:
      return bot.say(channel, "Poikkeuslista on tyhjä.")


def command_geo_remove(bot, user, channel, args):
  """.geo_remove nick!ident@hostname"""
  if get_op_status(user):
    if get_exempt_status(args):
      conn, c = open_DB()
      c.execute("DELETE FROM exceptions WHERE hostmask = '" + args + "';")
      conn.commit()
      conn.close()
      bot.say(channel, "Poikkeus poistettu.")
      command_geo_list(bot, user, channel, args)
      return True
    else:
      command_geo_list(bot, user, channel, args)
      bot.say(channel, "Virhe: hostmaskia ei löytynyt")


def get_op_status(user):
  if isAdmin(user):
    return True
  else:
    # käytetään authentikointiin qban_moduulin adminlistaa
    conn, c = open_DB(db="module_qban_ops.db")
    c.execute("SELECT hostmask FROM ops WHERE hostmask = '" + user + "' ")
    if c.fetchone():
      retval = True
    else:
      retval = False
    conn.close()
    return retval


def get_exempt_status(user):
  if isAdmin(user):
    return True
  else:
    if not "users.quakenet.org" in user:
      conn, c = open_DB()
      c.execute("SELECT hostmask FROM exceptions WHERE hostmask = '" + user + "' ")
      if c.fetchone():
        retval = True
      else:
        retval = False
      conn.close()
      return retval
    else:
      return True


def handle_userJoined(bot, user, channel):
  host = user.split('@')[1]
  try:
    country = gi4.country_name_by_name(host)
  except socket.gaierror:
    country = None
      
  if country != "Finland":
    if not get_exempt_status(user):
      banmask = "*!*@" + host
      banmask = banmask.encode('utf-8')
      nick = getNick(user)      
      bot.mode(channel, True, 'b', mask=banmask)
      bot.kick(channel, nick, "Hosted from a banned country (" + country + "). If you think you should have access, message the admins for an exempt.")   
      time.sleep(300)
      bot.mode(channel, False, 'b', mask=banmask)