from cStringIO import StringIO
import docx
from sqlalchemy import sql
from five import grok
from zope.i18n import translate
from z3c.saconfig import Session
from euphorie.client.survey import PathGhost
from euphorie.client.interfaces import IReportPhaseSkinLayer
from euphorie.client import MessageFactory as _
from euphorie.client.session import SessionManager
from euphorie.client import model


class ActionPlanReportDownload(grok.View):
    """Generate and download action report.
    """
    grok.context(PathGhost)
    grok.require("euphorie.client.ViewSurvey")
    grok.layer(IReportPhaseSkinLayer)
    grok.name("download")

    def update(self):
        self.session=SessionManager.session



    def getNodes(self):
        """Return an orderer list of all tree items for the current survey."""
        query=Session.query(model.SurveyTreeItem)\
                .filter(model.SurveyTreeItem.session==self.session)\
                .filter(sql.not_(model.SKIPPED_PARENTS))\
                .filter(sql.or_(model.MODULE_WITH_RISK_OR_TOP5_FILTER,
                                model.RISK_PRESENT_OR_TOP5_FILTER))\
                .order_by(model.SurveyTreeItem.path)
        return query.all()

    def addActionPlan(self, body):
        for node in self.getNodes():
            body.append(docx.heading(u"%s %s" % (node.number, node.title), (node.depth+1)))
            if node.type=="risk":
                pass


    def render(self):
        output=StringIO()
        relationships=docx.relationshiplist()
        document=docx.newdocument()
        body=document.xpath("/w:document/w:body", namespaces=docx.nsprefixes)[0]
        self.addActionPlan(body)
        coreprops=docx.coreproperties(
                title=self.session.title,
                subject="",
                creator=self.session.account.loginname,
                keywords=["OiRA"])
        appprops=docx.appproperties()
        contenttypes=docx.contenttypes()
        websettings=docx.websettings()
        wordrelationships=docx.wordrelationships(relationships)
        docx.savedocx(document, coreprops, appprops, contenttypes, websettings, wordrelationships, output)

        filename=_("filename_actionplan_report",
                   default=u"Action plan ${title}.docx",
                   mapping=dict(title=self.session.title))
        filename=translate(filename, context=self.request)
        self.request.response.setHeader("Content-Disposition",
                            u"attachment; filename=\"%s\"" % filename)
        self.request.response.setHeader("Content-Type", "application/msword")
        output.seek(0)
        return output.read()
