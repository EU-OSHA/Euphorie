from five import grok
from euphorie.client.company import CompanySchema
from euphorie.client.model import Company
from euphorie.client.api import JsonView
from euphorie.client.api import get_json_bool
from euphorie.client.api import get_json_string
from euphorie.client.api import get_json_token


class View(JsonView):
    grok.context(Company)
    grok.require('zope2.View')
    grok.name('index_html')

    def do_GET(self):
        company = self.context
        return {'type': 'company',
                'country': getattr(company, 'country', None),
                'employees': getattr(company, 'employees', None),
                'conductor': getattr(company, 'conductor', None),
                'referer': getattr(company, 'referer', None),
                'workers-participated':
                    getattr(company, 'workers_participated', None),
               }

    def do_POST(self):
        company = self.context
        try:
            company.country = get_json_string(self.input, 'country', False,
                    company.country, length=3)
            company.employees = get_json_token(self.input, 'employees',
                    CompanySchema['employees'], False, company.employees)
            company.conductor = get_json_token(self.input, 'conductor',
                    CompanySchema['conductor'], False, company.conductor)
            company.referer = get_json_token(self.input, 'referer',
                    CompanySchema['referer'], False, company.referer)
            company.workers_participated = get_json_bool(self.input,
                    'workers-participated', False,
                    company.workers_participated)
        except (KeyError, ValueError) as e:
            return {'result': 'error',
                    'message': str(e)}
        return self.do_GET()
