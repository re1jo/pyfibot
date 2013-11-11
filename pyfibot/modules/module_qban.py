# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, division
import codecs
import sys
import sqlite3
import re


def init(botconfig):
  open_DB(True)


def open_DB(createTable=False):
  conn = sqlite3.connect('module_qban_ops.db')
  c = conn.cursor()
  if createTable:
    c.execute('CREATE TABLE IF NOT EXISTS ops (hostmask);')
    conn.commit()
  return conn, c


def command_admin_add(bot, user, channel, args):
  """.admin_add nick!ident@hostname"""
  if get_op_status(user):
    if not get_op_status(args):
      conn, c = open_DB()
      insert = "INSERT INTO ops VALUES ('" + args + "');"
      c.execute(insert)
      conn.commit()
      conn.close()
      bot.say(channel, "Admin lisätty.")
      return True
    else:
      return bot.say(channel, "Virhe: Admin on jo listalla!")


def command_admin_list(bot, user, channel, args):
  if get_op_status(user):
    conn, c = open_DB()
    c.execute('SELECT hostmask FROM ops;')
    rows = c.fetchall()
    conn.close()
    if rows:
      ops = str("")
      j   = 0
      for i in rows:
        ops += "[" + i[0] + "] "
      return bot.say(channel, "Adminlista: " + ops)
    else:
      return bot.say(channel, "Adminlista on tyhjä.")


def command_admin_remove(bot, user, channel, args):
  """.admin_remove nick!ident@hostname"""
  if get_op_status(user):
    if get_op_status(args):
      conn, c = open_DB()
      c.execute("DELETE FROM ops WHERE hostmask = '" + args + "';")
      conn.commit()
      conn.close()
      bot.say(channel, "Admin poistettu.")
      command_admin_list(bot, user, channel, args)
      return True
    else:
      command_admin_list(bot, user, channel, args)
      bot.say(channel, "Virhe: hostmaskia ei löytynyt")


def get_op_status(user):
  if isAdmin(user):
     return True
  else:
    conn, c = open_DB()
    c.execute("SELECT hostmask FROM ops WHERE hostmask = '" + user + "' ")
    if c.fetchone():
      retval = True
    else:
      retval = False
    conn.close()
    return retval


def command_tempban(bot, user, channel, args):
  """.tempban #channel nick!ident@hostname 10minutes/1days/2weeks/1month syy"""
  if get_op_status(user):
    bot.say("Q!TheQBot@CServe.quakenet.org".encode('utf-8'), "tempban " + args)
    if channel != "#projekti_lol":
      nick = getNick(user)
      bot.say("#projekti_lol".encode('utf-8'), nick + " ajoi komennon: tempban " + args)


def command_unban(bot, user, channel, args):
  """.unban #channel nick!identi@hostname"""
  if get_op_status(user):    
    bot.say("Q!TheQBot@CServe.quakenet.org".encode('utf-8'), "unban " + args)
    if channel != "#projekti_lol":
      nick = getNick(user)    
      bot.say("#projekti_lol".encode('utf-8'), nick + " ajoi komennon: unban " + args)

#todo
#def command_listbans(bot, user, channel, args):
  #if get_op_status(user):