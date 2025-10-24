from .app_synchronizer import Synchronizer


class Metric:

    def __init__(self, kawa, reporter, description, name, sql, prompt, ai_mode=False, session_id=None):
        if (prompt is None) == (sql is None):
            raise Exception('Define one (And only one): query or prompt')

        self._k = kawa
        self._reporter = reporter
        self._name = name
        self._description = description
        self._sql = sql
        self._prompt = prompt
        self._ai_mode = ai_mode
        self._sessions_id = session_id

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def sql(self):
        return self._sql

    @property
    def prompt(self):
        return self._prompt

    def to_ascii(self):
        return f'"{self._name}"={self._sql or self._prompt}'.replace("SELECT", "")

    def sync(self, sheet):
        Metric._Synchronizer(
            kawa=self._k,
            ai_mode=self._ai_mode,
            session_id=self._sessions_id,
            metric=self,
            sheet=sheet
        ).sync()

        self._reporter.report(
            object_type='Metric',
            name=self._name,
        )

    class _Synchronizer(Synchronizer):

        def __init__(self, kawa, ai_mode, session_id, metric, sheet):
            super().__init__(
                kawa=kawa,
                icon='📐',
                entity_description=f'Metric "{metric.name}"',
            )
            self._metric = metric
            self._sheet = sheet
            self._ai_mode = ai_mode
            self._session_id = session_id

        def _load_state(self):
            if self._ai_mode:
                # State is not required in AI Mode, we will always be adding new adhoc columns
                return {}
            else:
                return {c['displayInformation']['displayName']: c for c in self._sheet['computedColumns'] if
                        c['columnNature'] == 'COMPUTATION'}

        def _raise_if_state_invalid(self):
            ...

        def _should_create(self) -> bool:
            if self._ai_mode:
                # Always create in AI Mode, because we create adHoc columns
                return True
            else:
                existing_formulas = self._state
                return self._metric.name not in existing_formulas

        def _create_new_entity(self):
            metric_definition = self._prepare_metric_definition()
            sheet_id = self._sheet['id']
            self._k.commands.run_command('addComputedColumnToSheet', {
                'sheetId': str(sheet_id),
                'displayInformation': {
                    'displayName': self._metric.name,
                    'description': self._metric.description,
                },
                'addInDefaultLayout': False,
                'adHoc': self._ai_mode,
                'aiContextId': self._session_id,
                **metric_definition,
            })

        def _update_entity(self):
            metric_definition = self._prepare_metric_definition()
            existing_formulas = self._state
            column_id = existing_formulas[self._metric.name]['columnId']
            sheet_id = self._sheet['id']
            self._k.commands.run_command('updateColumnXmlSyntacticTree', {
                'sheetId': str(sheet_id),
                'columnId': str(column_id),
                **metric_definition,
            })

        def _build_new_state(self):
            ...

        def _prepare_metric_definition(self):
            metric = self._metric
            sheet_id = self._sheet['id']
            if metric.prompt:
                generated_xml = self._k.post(
                    url=f'{self._k.kawa_api_url}/gen-ai/generate-xml-formula',
                    data={
                        'prompt': metric.prompt,
                        'sheetId': str(sheet_id),
                    }
                )['generatedXml']
                return {'xmlSyntacticTree': generated_xml}
            else:
                return {'sql': metric.sql}
