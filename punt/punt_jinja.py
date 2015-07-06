import os
import jinja2
from buildtarget import BuildTarget

from helpers import mkdir_recursive

class SimpleJinja(BuildTarget):

    def __init__(self, input_file="", output_file="", **kwargs):
        BuildTarget.__init__(self, **kwargs)

        self.input_file  = input_file
        self.output_file = output_file

        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(
                os.path.dirname(input_file)))

        self.input_basename = os.path.basename(self.input_file)

    def build(self, template_scripts="", template_styles=""):

        mkdir_recursive(os.path.dirname(self.output_file))

        template = self.jinja_env.get_template(self.input_basename)
        html = template.render(
            script_string=template_scripts,
            style_string=template_styles)

        with open(self.output_file, 'w') as template_output:
            template_output.write(html)

        return html
