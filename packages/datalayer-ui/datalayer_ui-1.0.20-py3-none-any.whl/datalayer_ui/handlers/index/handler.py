# Copyright (c) 2021-2024 Datalayer, Inc.
#
# Datalayer License

"""Index handler."""

import tornado

from datalayer_ui.handlers.base import BaseTemplateHandler


# pylint: disable=W0223
class IndexHandler(BaseTemplateHandler):
    """The handler for the index."""

    @tornado.web.authenticated
    def get(self):
        """The index page."""
        self.write(self.render_template("index.html"))
