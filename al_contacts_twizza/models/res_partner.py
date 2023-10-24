from odoo import fields, models, api
import base64
import os
import tempfile
import zipfile



class ResPartnerInherit(models.Model):
    _inherit = "res.partner"



    @api.model
    def download_base64_images(self):
        # Define your Odoo model and domain to select records
        model_name = 'product.template'
        domain = [('active', '=', True)]
        records = self.env[model_name].search(domain)
        
        # Create a temporary directory to store the images
        temp_dir = tempfile.mkdtemp()
        
        for record in self:
            base64_data = record.image_1024
        
            # Check if base64_data is a boolean value
            if isinstance(base64_data, bool):
                continue  # Skip this record if it's a boolean value
        
            decoded_data = base64.b64decode(base64_data)
            file_name = f'{record.id}_output_file.extension'
            file_path = os.path.join(temp_dir, file_name)
        
            try:
                with open(file_path, 'wb') as file:
                    file.write(decoded_data)
            except Exception as e:
                log(f"Error saving file: {str(e)}")
        
        # Create a zip archive
        zip_file_path = os.path.join(temp_dir, 'downloaded_images.zip')
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), temp_dir))
        
        # Clean up the temporary directory
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                os.remove(os.path.join(root, file))
        os.rmdir(temp_dir)
        
        # Save the zip archive as a binary field in a custom model (replace 'your.custom.model')
        zip_data = open(zip_file_path, 'rb').read()
        custom_model = record.env['x_images'].create({'name': 'Downloaded Images', 'x_studio_images': base64.encodestring(zip_data)})
        
        # Return an action to open the download link for the zip archive
        result = {
            'type': 'ir.actions.act_url',
            'url': '/web/binary/saveas?model=x_images&field=x_studio_images&id=%s&filename_field=name' % x_images.id,
            'target': 'new',
        }
        
        
            
