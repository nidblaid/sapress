from odoo import fields, models, api
from os import listdir, path
import pysftp
import logging

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ftp_host = fields.Char(string="FTP HOST", config_parameter='ftp_host')
    ftp_user = fields.Char(string="FTP USER", config_parameter='ftp_user')
    ftp_password = fields.Char(string="FTP PASSWORD", config_parameter='ftp_password')
    ftp_port = fields.Integer(string="FTP PORT", config_parameter='ftp_port', default=22)
    local_path = fields.Char(string="LOCAL PATH", config_parameter='local_path')
    remote_path = fields.Char(string="REMOTE PATH", config_parameter='remote_path')

    @api.model
    def _ftp_sync_database(self):
        ftp_host = self.env['ir.config_parameter'].sudo().get_param('ftp_host')
        ftp_user = self.env['ir.config_parameter'].sudo().get_param('ftp_user')
        ftp_password = self.env['ir.config_parameter'].sudo().get_param('ftp_password')
        ftp_port = self.env['ir.config_parameter'].sudo().get_param('ftp_port')
        db_dir = self.env['ir.config_parameter'].sudo().get_param('local_path')
        ftp_dir = self.env['ir.config_parameter'].sudo().get_param('remote_path')
        for db_file in listdir(db_dir):
            if db_file.endswith('.sql.gz'):
                server = pysftp.Connection(
                    host=ftp_host,
                    username=ftp_user,
                    password=ftp_password,
                    port=int(ftp_port)
                )
                local_path = path.join(db_dir, db_file)
                remote_path = path.join(ftp_dir, db_file)
                server.put(local_path, remote_path)
                _logger.info('--------------------------------')
                _logger.info('File sent to FTP server')
                _logger.info(local_path)
                _logger.info('--------------------------------')
                server.close()
        return True
