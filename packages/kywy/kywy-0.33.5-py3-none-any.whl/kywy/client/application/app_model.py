from .app_variable import Variable
from .app_metric import Metric
from .app_relationship import Relationship


class DataModel:

    def __init__(self, kawa, reporter, name, dataset=None, sheet=None, ai_mode=False, session_id=None):
        self._dataset = dataset
        self._name = name
        self._k = kawa
        self._ai_mode = ai_mode
        self._reporter = reporter
        self._relationships = []
        self._metrics = []
        self._variables = []
        self._selects = []
        self._created_grid_ids = []
        self._sheet = sheet
        self._session_id = session_id

    @property
    def sheet_id(self):
        return self._sheet['id'] if self._sheet else self._dataset.sheet_id

    @property
    def sheet(self):
        return self._sheet if self._sheet else self._dataset.sheet

    @property
    def name(self):
        return self._name

    @property
    def relationships(self):
        return self._relationships

    @property
    def metrics(self):
        return self._metrics

    def create_variable(self, name, kawa_type, initial_value):
        variable = Variable(
            kawa=self._k,
            reporter=self._reporter,
            sheet_id_supplier=lambda: self.sheet_id,
            name=name,
            kawa_type=kawa_type,
            initial_value=initial_value
        )
        self._variables.append(variable)

    def create_relationship(self,
                            name,
                            link,
                            description=None,
                            # These two are synonyms
                            dataset=None, origin_model=None,
                            target_model=None,
                            ):
        rel = Relationship(
            kawa=self._k,
            reporter=self._reporter,
            model=self,
            name=name,
            description=description,
            dataset=dataset or origin_model,
            target_sheet=target_model.sheet if target_model else None,
            link=link,
            ai_mode=self._ai_mode,
            session_id=self._session_id,
        )
        self._relationships.append(rel)
        return rel

    def create_metric(self, name, description=None, formula=None, prompt=None, **kwargs):

        sql = None
        if formula:
            normalized = formula.strip().upper()
            if not normalized.startswith("SELECT"):
                sql = f"SELECT {formula}"
            else:
                sql = formula

        self._metrics.append(
            Metric(
                kawa=self._k,
                reporter=self._reporter,
                name=name,
                description=description or sql or prompt,
                sql=sql,
                prompt=prompt,
                ai_mode=self._ai_mode,
                session_id=self._session_id,
            )
        )

    def select(self, *columns_or_column_names):
        select = self._k.sheet(sheet_id=self.sheet_id).select(*columns_or_column_names).session(self._session_id)
        self._selects.append(select)
        return select

    def create_views(self):
        i = 1
        for select in self._selects:
            created_grid = select.as_grid(
                standalone=False
            )
            self._created_grid_ids.append(created_grid['id'])
            i += 1

        return self._created_grid_ids

    def sync(self):
        for rel in self._relationships:
            rel.sync()

        for var in self._variables:
            var.sync()

        for metric in self._metrics:
            metric.sync(sheet=self.sheet)
