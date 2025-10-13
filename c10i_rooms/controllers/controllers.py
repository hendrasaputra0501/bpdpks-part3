# -*- coding: utf-8 -*-
# from odoo import http


# class Room(http.Controller):
#     @http.route('/room/room/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/room/room/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('room.listing', {
#             'root': '/room/room',
#             'objects': http.request.env['room.room'].search([]),
#         })

#     @http.route('/room/room/objects/<model("room.room"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('room.object', {
#             'object': obj
#         })
