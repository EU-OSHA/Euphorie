from cStringIO import StringIO
import docx
import htmllaundry
from sqlalchemy import sql
from five import grok
from zope.i18n import translate
from z3c.saconfig import Session
from plonetheme.nuplone.utils import formatDate
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


    def addIntroduction(self, body):
        p=translate(_("plan_report_intro_1", default=
            u"By filling in the list of questions, you have completed a risk "
            u"assessment. This assessment is used to draw up an action plan. "
            u"The progress of this action plan must be discussed annually and "
            u"a small report must be written on the progress. Certain "
            u"subjects might have been completed and perhaps new subjects "
            u"need to be added."), context=self.request)
        body.append(docx.paragraph(p))

        if self.session.report_comment:
            body.append(docx.paragraph(self.session.report_comment))


    def addActionPlan(self, body):
        survey=self.request.survey
        t=lambda txt: translate(txt, context=self.request)
        for node in self.getNodes():
            body.append(docx.heading(u"%s %s" % (node.number, node.title), (node.depth+1)))

            if node.type!="risk":
                continue

            zodb_node=survey.restrictedTraverse(node.zodb_path.split("/"))
            if node.identification=="no" and not (
                    zodb_node.problem_description and zodb_node.problem_description.strip()):
                body.append(docx.paragraph(t(_("warn_risk_present", default=u"You responded negative to the above statement."))))
            elif node.postponed or not node.identification:
                body.append(docx.paragraph(t(_("risk_unanswered", default=u"This risk still needs to be inventorised."))))

            if node.priority:
                if node.priority=="low":
                    level=_("report_priority_low", default=u"low priority risk")
                elif node.priority=="medium":
                    level=_("report_priority_medium", default=u"medium priority risk")
                elif node.priority=="high":
                    level=_("report_priority_high", default=u"high priority risk")
                body.append(docx.paragraph(
                    [(t(_("report_priority", default=u"This is a ")), ""),
                     (t(level), "b")]))

            body.append(docx.paragraph(htmllaundry.StripMarkup(zodb_node.description)))

            for (idx, measure) in enumerate(node.action_plans):
                if len(node.action_plans)==1:
                    body.append(docx.heading(t(_("header_measure_single", default=u"Measure")), 4))
                else:
                    body.append(docx.heading(t(_("header_measure_multiple", default=u"Measure ${index}",
                        mapping={"index": idx+1})), 4))
                self.addMeasure(body, measure)


    def addMeasure(self, body, measure):
        t=lambda txt: translate(txt, context=self.request)
        table=[]
        if measure.action_plan:
            table.append([t(_("report_measure_actionplan", default=u"Action plan:")), measure.action_plan])
        if measure.prevention_plan:
            table.append([t(_("report_measure_preventionplan", default=u"Prevention plan:")), measure.prevention_plan])
        if measure.requirements:
            table.append([t(_("report_measure_requirements", default=u"Requirements:")), measure.requirements])
        if table:
            body.append(docx.table(table, False))

        if measure.responsible and not (measure.planning_start or measure.planning_end):
            body.append(docx.paragraph(t(_(u"${responsible} is responsible for this task.",
                mapping={"responsible": measure.responsible}))))
        elif measure.responsible and measure.planning_start and not measure.planning_end:
            body.append(docx.paragraph(t(_(u"${responsible} is responsible for this task which starts on ${start}.",
                mapping={"responsible": measure.responsible,
                         "start": formatDate(self.request, measure.planning_start)}))))
        elif measure.responsible and not measure.planning_start and measure.planning_end:
            body.append(docx.paragraph(t(_(u"${responsible} is responsible for this task which ends on ${end}.",
                mapping={"responsible": measure.responsible,
                         "end": formatDate(self.request, measure.planning_end)}))))
        elif measure.responsible and measure.planning_start and measure.planning_end:
            body.append(docx.paragraph(t(_(u"${responsible} is responsible for this task which starts on ${start} and ends on ${end}.",
                mapping={"responsible": measure.responsible,
                         "start": formatDate(self.request, measure.planning_start),
                         "end": formatDate(self.request, measure.planning_end)}))))
        elif not measure.responsible and measure.planning_start and not measure.planning_end:
            body.append(docx.paragraph(t(_(u"This task starts at ${start}.",
                mapping={"start": formatDate(self.request, measure.planning_start)}))))
        elif not measure.responsible and not measure.planning_start and measure.planning_end:
            body.append(docx.paragraph(t(_(u"This task ends at ${end}.",
                mapping={"end": formatDate(self.request, measure.planning_end)}))))
        elif not measure.responsible and measure.planning_start and measure.planning_end:
            body.append(docx.paragraph(t(_(u"This task starts at ${start} and ends at ${end}.",
                mapping={"start": formatDate(self.request, measure.planning_start),
                         "end": formatDate(self.request, measure.planning_end)}))))


    def render(self):
        output=StringIO()
        relationships=docx.relationshiplist()
        document=docx.newdocument()
        body=document.xpath("/w:document/w:body", namespaces=docx.nsprefixes)[0]
        self.addIntroduction(body)
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

        filename=_("filename_report_actionplan",
                   default=u"Action plan ${title}.docx",
                   mapping=dict(title=self.session.title))
        filename=translate(filename, context=self.request)
        self.request.response.setHeader("Content-Disposition",
                            u"attachment; filename=\"%s\"" % filename)
        self.request.response.setHeader("Content-Type",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        output.seek(0)
        return output.read()
