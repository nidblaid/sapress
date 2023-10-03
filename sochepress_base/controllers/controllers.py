# -*- coding: utf-8 -*-

# class SchoolMaintenance(http.Controller):
#     @http.route('/school_maintenance/school_maintenance/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/school_maintenance/school_maintenance/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('school_maintenance.listing', {
#             'root': '/school_maintenance/school_maintenance',
#             'objects': http.request.env[
#             'school_maintenance.school_maintenance'].search([]),
#         })

#     @http.route('/school_maintenance/school_maintenance/objects/<model(
#     "school_maintenance.school_maintenance"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('school_maintenance.object', {
#             'object': obj
#         })
