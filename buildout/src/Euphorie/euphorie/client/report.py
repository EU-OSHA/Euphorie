from cStringIO import StringIO
import htmllaundry
from rtfng.Elements import Document
from rtfng.Elements import StyleSheet
from rtfng.document.paragraph import Paragraph
from rtfng.document.section import Section
from rtfng.Renderer import Renderer
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


    def addIntroduction(self, document):
        intro=translate(_("plan_report_intro_1", default=
            u"By filling in the list of questions, you have completed a risk "
            u"assessment. This assessment is used to draw up an action plan. "
            u"The progress of this action plan must be discussed annually and "
            u"a small report must be written on the progress. Certain "
            u"subjects might have been completed and perhaps new subjects "
            u"need to be added."), context=self.request)

        section=Section()
        document.Sections.append(section)

        normal_style=document.StyleSheet.ParagraphStyles.Normal
        section.append(Paragraph(normal_style, intro))

        if self.session.report_comment:
            section.append(Paragraph(normal_style, self.session.report_comment))


    def addActionPlan(self, document):
        section=Section()
        document.Sections.append(section)
        survey=self.request.survey
        t=lambda txt: translate(txt, context=self.request)

        normal_style=document.StyleSheet.ParagraphStyles.Normal
        warning_style=document.StyleSheet.ParagraphStyles.Warning
        measure_heading_style=document.StyleSheet.ParagraphStyles.MeasureHeading
        header_styles={
                0: document.StyleSheet.ParagraphStyles.Heading2,
                1:  document.StyleSheet.ParagraphStyles.Heading3,
                2:  document.StyleSheet.ParagraphStyles.Heading4,
                3:  document.StyleSheet.ParagraphStyles.Heading5,
                }

        for node in self.getNodes():
            section.append(Paragraph(header_styles[node.depth], u"%s %s" % (node.number, node.title)))

            if node.type!="risk":
                continue

            zodb_node=survey.restrictedTraverse(node.zodb_path.split("/"))
            if node.identification=="no" and not (
                    zodb_node.problem_description and zodb_node.problem_description.strip()):
                section.append(Paragraph(warning_style,
                    t(_("warn_risk_present", default=u"You responded negative to the above statement."))))
            elif node.postponed or not node.identification:
                section.append(Paragraph(warning_style,
                    t(_("risk_unanswered", default=u"This risk still needs to be inventorised."))))

            if node.priority:
                if node.priority=="low":
                    level=_("report_priority_low", default=u"low priority risk")
                elif node.priority=="medium":
                    level=_("report_priority_medium", default=u"medium priority risk")
                elif node.priority=="high":
                    level=_("report_priority_high", default=u"high priority risk")
                section.append(Paragraph(normal_style, 
                    t(_("report_priority", default=u"This is a ")), t(level)))

            section.append(Paragraph(normal_style, htmllaundry.StripMarkup(zodb_node.description)))

            for (idx, measure) in enumerate(node.action_plans):
                if len(node.action_plans)==1:
                    section.append(Paragraph(measure_heading_style,
                        t(_("header_measure_single", default=u"Measure"))))
                else:
                    section.append(Paragraph(measure_heading_style,
                        t(_("header_measure_multiple", default=u"Measure ${index}", mapping={"index": idx+1}))))
                self.addMeasure(document, section, measure)


    def addMeasure(self, document, section, measure):
        normal_style=document.StyleSheet.ParagraphStyles.Normal

        t=lambda txt: translate(txt, context=self.request)
        table=[]
        if measure.action_plan:
            table.append([t(_("report_measure_actionplan", default=u"Action plan:")), measure.action_plan])
        if measure.prevention_plan:
            table.append([t(_("report_measure_preventionplan", default=u"Prevention plan:")), measure.prevention_plan])
        if measure.requirements:
            table.append([t(_("report_measure_requirements", default=u"Requirements:")), measure.requirements])
#        if table:
#            body.append(docx.table(table, False))

        if measure.responsible and not (measure.planning_start or measure.planning_end):
            section.append(Paragraph(normal_style, 
                t(_(u"${responsible} is responsible for this task.", mapping={"responsible": measure.responsible}))))
        elif measure.responsible and measure.planning_start and not measure.planning_end:
            section.append(Paragraph(normal_style, 
                t(_(u"${responsible} is responsible for this task which starts on ${start}.",
                    mapping={"responsible": measure.responsible,
                             "start": formatDate(self.request, measure.planning_start)}))))
        elif measure.responsible and not measure.planning_start and measure.planning_end:
            section.append(Paragraph(normal_style, 
                t(_(u"${responsible} is responsible for this task which ends on ${end}.",
                    mapping={"responsible": measure.responsible,
                             "end": formatDate(self.request, measure.planning_end)}))))
        elif measure.responsible and measure.planning_start and measure.planning_end:
            section.append(Paragraph(normal_style, 
                t(_(u"${responsible} is responsible for this task which starts on ${start} and ends on ${end}.",
                    mapping={"responsible": measure.responsible,
                             "start": formatDate(self.request, measure.planning_start),
                             "end": formatDate(self.request, measure.planning_end)}))))
        elif not measure.responsible and measure.planning_start and not measure.planning_end:
            section.append(Paragraph(normal_style, 
                t(_(u"This task starts at ${start}.",
                    mapping={"start": formatDate(self.request, measure.planning_start)}))))
        elif not measure.responsible and not measure.planning_start and measure.planning_end:
            section.append(Paragraph(normal_style, 
                t(_(u"This task ends at ${end}.", mapping={"end": formatDate(self.request, measure.planning_end)}))))
        elif not measure.responsible and measure.planning_start and measure.planning_end:
            section.append(Paragraph(normal_style, 
                t(_(u"This task starts at ${start} and ends at ${end}.",
                    mapping={"start": formatDate(self.request, measure.planning_start),
                             "end": formatDate(self.request, measure.planning_end)}))))


    def createDocument(self):
        from rtfng.Styles import TextStyle
        from rtfng.Styles import ParagraphStyle
        from rtfng.PropertySets import TextPropertySet
        from rtfng.PropertySets import ParagraphPropertySet
        stylesheet=StyleSheet()

        style=TextStyle(TextPropertySet(stylesheet.Fonts.Arial, 22))

        stylesheet.ParagraphStyles.append(ParagraphStyle("Normal",
            style.Copy(), ParagraphPropertySet(space_before=60, space_after=60)))

        style.textProps.italic=True
        stylesheet.ParagraphStyles.append(ParagraphStyle("Warning",
            style.Copy(), ParagraphPropertySet(space_before=10, space_after=10)))

        style.textProps.italic=False
        style.textProps.size=32
        stylesheet.ParagraphStyles.append(ParagraphStyle("Heading 1",
            style.Copy(), ParagraphPropertySet(space_before=240, space_after=60)))

        style.textProps.size=24
        stylesheet.ParagraphStyles.append(ParagraphStyle("Heading 2",
            style.Copy(), ParagraphPropertySet(space_before=240, space_after=60)))
        stylesheet.ParagraphStyles.append(ParagraphStyle("Heading 3",
            style.Copy(), ParagraphPropertySet(space_before=240, space_after=60)))
        stylesheet.ParagraphStyles.append(ParagraphStyle("Heading 4",
            style.Copy(), ParagraphPropertySet(space_before=240, space_after=60)))
        stylesheet.ParagraphStyles.append(ParagraphStyle("Heading 5",
            style.Copy(), ParagraphPropertySet(space_before=240, space_after=60)))


        style.textProps.bold=True
        stylesheet.ParagraphStyles.append(ParagraphStyle("Measure Heading",
            style.Copy(), ParagraphPropertySet(space_before=60, space_after=20)))

        document=Document(stylesheet)
        return document

    def render(self):
        document=self.createDocument()
        self.addIntroduction(document)

        renderer=Renderer()
        output=StringIO()
        renderer.Write(document, output)


#        self.addActionPlan(body)

        filename=_("filename_report_actionplan",
                   default=u"Action plan ${title}",
                   mapping=dict(title=self.session.title))
        filename=translate(filename, context=self.request)
        self.request.response.setHeader("Content-Disposition",
                            u"attachment; filename=\"%s.rtf\"" % filename)
        self.request.response.setHeader("Content-Type", "application/rtf")
        output.seek(0)
        return output.read()
