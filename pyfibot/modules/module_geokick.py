# -*- coding: utf-8 -*-
import sys
import pygeoip
import os.path
import socket
import sqlite3
import time
import re

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
  """.geo_exempt nick!ident@hostname | Supports wildcards, for example *!*@*site.com (! and @ are required)"""
  if get_op_status(user):
    if not get_exempt_status(args):
      if len(args) < 4:
        conn, c = open_DB()
        insert = "INSERT INTO exceptions VALUES ('" + args + "');"
        c.execute(insert)
        conn.commit()
        conn.close()
        bot.say(channel, "Success: " + args.encode('utf-8') + " added to exempt list.")
        return True
      else:
        return bot.say(channel, "Error: invalid exempt. See .help geo_exempt")  
    else:
      return bot.say(channel, "Error: exempt exists already!")


def command_geo_list(bot, user, channel, args):
  if get_op_status(user):
    conn, c = open_DB()
    c.execute('SELECT hostmask FROM exceptions;')
    rows = c.fetchall()
    conn.close()
    if rows:
      excepts = str("")
      for i in rows:
        excepts += "[" + i[0] + "] "
      return bot.say(channel, "Exceptions: " + excepts)
    else:
      return bot.say(channel, "Error: no exceptions added. See .help geo_exempt")


def command_geo_remove(bot, user, channel, args):
  """.geo_remove hostname"""
  if get_op_status(user):
    conn, c = open_DB()
    c.execute("SELECT hostmask FROM exceptions WHERE hostmask = '" + args + "'")
    if c.fetchone():
      conn, c = open_DB()
      c.execute("DELETE FROM exceptions WHERE hostmask = '" + args + "'")
      conn.commit()
      conn.close()
      bot.say(channel, "Success: exception removed.")
    else:
      bot.say(channel, "Error: hostmask not found. Check .geo_list for broader exempts that would override what you are trying to add.")


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


# try to split user string as dictionary with nick, ident and hostname
def get_data(user):
  try:
    temp = user.split('@')[0]
    data = {'nick':getNick(user), 'ident':temp.split('!')[1], 'host':user.split('@')[1]  }
    return data
  except:
    return False


#@todo blacklist = ['elisa-mobile.fi', 'nat-elisa-mobile.fi']
def get_exempt_status(user):
  if isAdmin(user):
    return True
  else:
    data = get_data(user)

    if data:
      conn, c = open_DB()
      c.execute('SELECT hostmask FROM exceptions;')
      rows = c.fetchall()
      conn.close()

      # iterate all hostmasks
      for i in rows:
        row = get_data(i[0])
        j = 0

        # check current row data against that of the user data
        for row_value in row.values():
          for data_value in data.values():
            # if a wildcard or exact match
            if row_value == "*" or ( row_value in data_value and "*" not in row_value ):
              j += 1
              break
            # if contains a wildcard, we have to regex
            elif "*" in row_value:
              regex = re.escape(row_value)
              regex = row_value.replace("*",".*")
              if re.search(regex, data_value):
                j += 1
                break

          # if counter reaches three, user matches exception list
          if j == 3:
            return True
  return False


def handle_userJoined(bot, user, channel):
  # if tested user is in exception list
  if not get_exempt_status(user):
    host = user.split('@')[1]

    # attempt to get location data from the geoip database
    try:
      country = gi4.country_name_by_name(host)
    except socket.gaierror:
      country = None

    # if country information was found & if it wasn't Finland
    if country != "Finland" and country != "":
      # grab nickname and hostname of the user
      nick = getNick(user)
      banmask = "*!*@" + host
      banmask = banmask.encode('utf-8')

      # ban & kick
      bot.mode(channel, True, 'b', mask=banmask)
      bot.kick(channel, nick, "Hosted from a banned country (" + country + ") or host (" + host + "). If you think you should have access, /msg lolfi .request_exempt")

      # unban after 300s to avoid filling the banlist
      time.sleep(300)
      bot.mode(channel, False, 'b', mask=banmask)


def command_request_exempt(bot, user, channel, args):
  if channel != "#projekti_lol":
    nick = getNick(user)
    bot.say("#projekti_lol".encode('utf-8'), "Notification: " + nick + " (" + user + ") requested and exempt.")
