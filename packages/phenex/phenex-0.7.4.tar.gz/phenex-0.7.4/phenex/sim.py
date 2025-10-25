from typing import Dict
from phenex.mappers import DomainsDictionary
from phenex.tables import PhenexTable
import pandas as pd
import numpy as np
import ibis
from datetime import datetime, timedelta


class DomainsMocker:
    """
    DomainsMocker immitates healthcare data domains for testing purposes. The mock data is NOT FIT FOR SIMULATION. The data reflect the basic structure of the data without caring too much about accurate statistics. The statistics are generally chosen to be reasonable (e.g. Poisson, Gaussian, log-normal as appropriate), and the content is domain-appropriate (e.g. using relevant codes/code types) but we are NOT trying to accurately model real data.

    Note that DomainsMocker only supports OMOP structured data due to current license restrictions of other data formats.

    Args:
        domains_dict: The domains dictionary containing table mappers that define which tables to mock
        n_patients: Number of patients to simulate. Defaults to 10000.
        random_seed: Random seed for reproducible results. Defaults to 42.
    """

    def __init__(
        self,
        domains_dict: DomainsDictionary,
        n_patients: int = 10000,
        random_seed: int = 42,
    ):
        self.domains_dict = domains_dict
        self.n_patients = n_patients
        self.random_seed = random_seed

        # Set random seeds for reproducible results
        np.random.seed(random_seed)
        import random

        random.seed(random_seed)

        # Generate base patient IDs that look more realistic (7-8 digit numbers)
        self.base_patient_ids = self._generate_person_ids(n_patients, base=1000000)

        # Pre-generate visit detail IDs for consistency across tables
        self._visit_detail_ids_pool = None

        # Pre-generate visit occurrence IDs for consistency across tables
        self._visit_occurrence_ids_pool = None

        # Cache for source tables to ensure consistent data on multiple calls
        self._cached_source_tables = None

        # Cache for person birth years for consistency across tables
        self._person_birth_years = None

        # Cache for death data for consistency across tables
        self._death_data = None

    def _generate_dates_within_lifespan(
        self,
        person_ids: np.ndarray,
        count: int,
        min_year: int = 2014,
        max_year: int = 2024,
        hour_range: tuple = (0, 24),
    ) -> tuple[list, list]:
        """
        Generate random dates that respect patient birth and death dates.

        Args:
            person_ids: Array of person IDs for each record
            count: Total number of dates to generate
            min_year: Minimum year for date range (overridden by birth year + 1)
            max_year: Maximum year for date range (overridden by death date)
            hour_range: Tuple of (min_hour, max_hour) for datetime generation

        Returns:
            Tuple of (dates, datetimes) lists
        """
        birth_years = self._get_person_birth_years()
        death_data = self._mock_death_table()

        # Map each record to its patient's birth year (vectorized)
        # Find the patient index for each person_id by looking it up in base_patient_ids
        patient_id_to_index = {
            pid: idx for idx, pid in enumerate(self.base_patient_ids)
        }
        patient_indices = np.array([patient_id_to_index[pid] for pid in person_ids])
        record_birth_years = birth_years[patient_indices]

        # Calculate start dates for each record (fully vectorized)
        # Start year: max of (birth year + 1, min_year)
        record_min_years = np.maximum(record_birth_years + 1, min_year)
        record_min_dates = pd.to_datetime(dict(year=record_min_years, month=1, day=1))

        # Calculate end dates (vectorized) - default to max year
        default_max_date = pd.to_datetime(f"{max_year}-12-31")
        record_max_dates = pd.Series([default_max_date] * count)

        # Apply death dates (vectorized lookup if there are deaths)
        if len(death_data) > 0:
            # Convert death dates to pandas timestamps for consistent comparison
            death_df = pd.DataFrame(
                {
                    "PERSON_ID": death_data["PERSON_ID"],
                    "DEATH_DATE": pd.to_datetime(death_data["DEATH_DATE"]),
                }
            )

            # Create DataFrame with record person IDs for merging
            record_df = pd.DataFrame({"idx": range(count), "PERSON_ID": person_ids})

            # Left join to get death dates (NaT for living patients)
            merged = record_df.merge(death_df, on="PERSON_ID", how="left")

            # Fill NaT values with default max date, then take minimum (fully vectorized)
            death_dates = merged["DEATH_DATE"].fillna(default_max_date)

            # Vectorized minimum operation
            record_max_dates = pd.Series(death_dates).combine(
                pd.Series([default_max_date] * count), min
            )

        # Ensure valid date ranges (vectorized)
        invalid_mask = record_min_dates >= record_max_dates
        record_max_dates[invalid_mask] = record_min_dates[invalid_mask] + pd.Timedelta(
            days=1
        )

        # Use vectorized date generation with per-record ranges
        generated_dates, generated_datetimes = (
            self._generate_random_datetimes_vectorized(
                count,
                start_dates=record_min_dates,
                end_dates=record_max_dates,
                hour_range=hour_range,
            )
        )

        # Additional safety check: ensure no generated dates violate death constraints
        if len(death_data) > 0:
            death_lookup = dict(
                zip(death_data["PERSON_ID"], pd.to_datetime(death_data["DEATH_DATE"]))
            )
            for i, (person_id, gen_date) in enumerate(zip(person_ids, generated_dates)):
                if person_id in death_lookup:
                    death_date = death_lookup[person_id]
                    if pd.to_datetime(gen_date) > death_date:
                        # Force the date to be valid by setting it to death date minus 1 day
                        valid_date = death_date - pd.Timedelta(days=1)
                        generated_dates[i] = valid_date.date()
                        generated_datetimes[i] = generated_datetimes[i].replace(
                            year=valid_date.year,
                            month=valid_date.month,
                            day=valid_date.day,
                        )

        return generated_dates, generated_datetimes

    def _generate_random_datetimes_vectorized(
        self,
        count: int,
        start_date=None,
        end_date=None,
        start_dates=None,
        end_dates=None,
        hour_range: tuple = (0, 24),
    ) -> tuple:
        """
        Generate random dates and datetimes in a highly optimized vectorized way.

        Can handle either uniform date ranges or per-record date ranges for
        respecting individual patient birth/death constraints.

        Args:
            count: Number of datetime pairs to generate
            start_date: Single start date for uniform range (or None)
            end_date: Single end date for uniform range (or None)
            start_dates: Array of start dates for per-record ranges (or None)
            end_dates: Array of end dates for per-record ranges (or None)
            hour_range: Tuple of (min_hour, max_hour) for time generation

        Returns:
            tuple: (dates_list, datetimes_list)
        """
        if count == 0:
            return [], []

        # Generate random hours and minutes for all records
        random_hours = np.random.randint(hour_range[0], hour_range[1], size=count)
        random_minutes = np.random.randint(0, 60, size=count)

        if start_dates is not None and end_dates is not None:
            # Per-record date ranges (vectorized approach for patient lifespan constraints)
            start_dates_pd = pd.to_datetime(start_dates)
            end_dates_pd = pd.to_datetime(end_dates)

            # Calculate date ranges in days for each record
            date_ranges = (end_dates_pd - start_dates_pd).dt.days

            # Ensure minimum 1 day range to avoid division by zero
            date_ranges = np.maximum(date_ranges, 1)

            # Generate random days within each record's valid range
            random_day_fractions = np.random.random(size=count)
            random_days = (random_day_fractions * date_ranges).astype(int)

            # Generate base dates by adding random days to start dates
            base_dates = start_dates_pd + pd.to_timedelta(random_days, unit="days")
        else:
            # Uniform date range (original behavior)
            if start_date is None or end_date is None:
                raise ValueError(
                    "Must provide either (start_date, end_date) or (start_dates, end_dates)"
                )

            # Calculate date range in days
            date_range = (end_date - start_date).days

            # Generate random days for uniform range
            random_days = np.random.uniform(0, date_range, size=count).astype(int)

            # Generate dates as pandas DatetimeIndex for speed, then convert
            base_dates = pd.to_datetime(start_date) + pd.to_timedelta(
                random_days, unit="days"
            )

        # Add hours and minutes
        datetimes = (
            base_dates
            + pd.to_timedelta(random_hours, unit="hours")
            + pd.to_timedelta(random_minutes, unit="minutes")
        )

        # Convert to Python datetime objects
        dates_list = [dt.date() for dt in base_dates]
        datetimes_list = [dt.to_pydatetime() for dt in datetimes]

        return dates_list, datetimes_list

    def _generate_person_ids(self, count: int, base: int = 1000000) -> np.ndarray:
        """
        Generate realistic-looking person IDs.

        Args:
            count (int): Number of IDs to generate
            base (int): Base number to start from (default: 1M for 7-8 digit IDs)

        Returns:
            np.ndarray: Array of realistic-looking IDs
        """
        # Generate IDs that look realistic but are still deterministic given the seed
        ids = (
            base + np.arange(count) * np.random.randint(3, 47, size=1)[0]
        )  # Random step between 3-47
        ids += np.random.randint(0, 999, size=count)  # Add some random noise
        return ids

    def _mock_person_table(self) -> pd.DataFrame:
        """
        Mock the PERSON table with OMOP schema.

        Returns:
            pd.DataFrame: Mocked person table data
        """
        # Gender: roughly 50/50 split with OMOP concept IDs
        gender_concepts = np.random.choice(
            [8507, 8532], size=self.n_patients, p=[0.51, 0.49]
        )  # Female, Male
        gender_source_values = np.where(gender_concepts == 8507, "F", "M")

        # Birth years: use the cached birth years to ensure consistency with death table
        birth_years = self._get_person_birth_years()

        # Birth months and days
        birth_months = np.random.randint(1, 13, size=self.n_patients)
        birth_days = np.random.randint(
            1, 29, size=self.n_patients
        )  # Keep it simple, avoid month/day complications

        # Birth datetime
        birth_datetimes = pd.to_datetime(
            {"year": birth_years, "month": birth_months, "day": birth_days}
        )

        # Race concepts (US demographics roughly)
        race_concepts = np.random.choice(
            [
                8527,
                8516,
                8515,
                8557,
                0,
            ],  # White, Black, Asian, Native American, Unknown
            size=self.n_patients,
            p=[0.72, 0.13, 0.06, 0.01, 0.08],
        )
        race_source_values = np.select(
            [
                race_concepts == 8527,
                race_concepts == 8516,
                race_concepts == 8515,
                race_concepts == 8557,
                race_concepts == 0,
            ],
            [
                "White",
                "Black or African American",
                "Asian",
                "American Indian or Alaska Native",
                "Unknown",
            ],
            default="Other",
        )

        # Ethnicity concepts
        ethnicity_concepts = np.random.choice(
            [38003563, 38003564, 0],  # Hispanic, Not Hispanic, Unknown
            size=self.n_patients,
            p=[0.18, 0.79, 0.03],
        )
        ethnicity_source_values = np.select(
            [
                ethnicity_concepts == 38003563,
                ethnicity_concepts == 38003564,
                ethnicity_concepts == 0,
            ],
            ["Hispanic or Latino", "Not Hispanic or Latino", "Unknown"],
            default="Other",
        )

        # Optional fields - some patients will have these, others won't
        location_ids = np.where(
            np.random.random(self.n_patients) < 0.7,  # 70% have location
            self._generate_person_ids(self.n_patients, base=200000)[
                : self.n_patients
            ],  # 6-7 digit location IDs
            np.nan,
        )

        provider_ids = np.where(
            np.random.random(self.n_patients) < 0.8,  # 80% have provider
            self._generate_person_ids(self.n_patients, base=800000)[
                : self.n_patients
            ],  # 6-7 digit provider IDs
            np.nan,
        )

        care_site_ids = np.where(
            np.random.random(self.n_patients) < 0.6,  # 60% have care site
            self._generate_person_ids(self.n_patients, base=300000)[
                : self.n_patients
            ],  # 6-7 digit care site IDs
            np.nan,
        )

        # Person source values (often medical record numbers)
        person_source_values = [f"MRN{pid:08d}" for pid in self.base_patient_ids]

        return pd.DataFrame(
            {
                "PERSON_ID": self.base_patient_ids,
                "GENDER_CONCEPT_ID": gender_concepts,
                "YEAR_OF_BIRTH": birth_years,
                "MONTH_OF_BIRTH": birth_months,
                "DAY_OF_BIRTH": birth_days,
                "BIRTH_DATETIME": birth_datetimes,
                "RACE_CONCEPT_ID": race_concepts,
                "ETHNICITY_CONCEPT_ID": ethnicity_concepts,
                "LOCATION_ID": location_ids,
                "PROVIDER_ID": provider_ids,
                "CARE_SITE_ID": care_site_ids,
                "PERSON_SOURCE_VALUE": person_source_values,
                "GENDER_SOURCE_VALUE": gender_source_values,
                "GENDER_SOURCE_CONCEPT_ID": gender_concepts,  # Same as gender_concept_id for simplicity
                "RACE_SOURCE_VALUE": race_source_values,
                "RACE_SOURCE_CONCEPT_ID": race_concepts,  # Same as race_concept_id for simplicity
                "ETHNICITY_SOURCE_VALUE": ethnicity_source_values,
                "ETHNICITY_SOURCE_CONCEPT_ID": ethnicity_concepts,  # Same as ethnicity_concept_id for simplicity
            }
        )

    def _generate_birth_year_probs(self) -> np.ndarray:
        """Generate realistic birth year probabilities (more recent years more later)."""
        years = np.arange(1930, 2011)
        # Exponential-like distribution favoring more recent years
        probs = np.exp((years - 1930) * 0.02)
        return probs / probs.sum()

    def _mock_condition_occurrence_table(self) -> pd.DataFrame:
        """
        Mock the CONDITION_OCCURRENCE table with OMOP schema.

        Returns:
            pd.DataFrame: Mocked condition occurrence table data
        """
        # Generate conditions for patients - use Poisson distribution for number of conditions per patient
        conditions_per_patient = np.random.poisson(
            lam=3.5, size=self.n_patients
        )  # Average 3-4 conditions per patient
        conditions_per_patient = np.clip(
            conditions_per_patient, 0, 20
        )  # Cap at 20 conditions

        total_conditions = conditions_per_patient.sum()

        # Generate condition occurrence IDs that look realistic
        condition_occurrence_ids = self._generate_person_ids(
            total_conditions, base=50000000
        )  # 8-digit IDs

        # Generate person IDs based on conditions per patient
        person_ids = np.repeat(self.base_patient_ids, conditions_per_patient)

        # Common condition concept IDs with tutorial-relevant codes
        # Include codes from codelists_for_tutorial.csv for ATRIAL_FIBRILLATION and MYOCARDIAL_INFARCTION
        common_condition_concepts = [
            201820,  # Diabetes mellitus
            316866,  # Hypertensive disorder
            440383,  # Depressive disorder
            432867,  # Asthma
            321596,  # Cough
            378253,  # Headache
            134736,  # Back pain (changed from 312327 to avoid conflict)
            4170143,  # Chest pain
            200219,  # Pneumonia
            # ATRIAL_FIBRILLATION codes from tutorial codelists
            1569171,  # Chronic atrial fibrillation
            4232691,  # Permanent atrial fibrillation
            4154290,  # Paroxysmal atrial fibrillation
            4232697,  # Persistent atrial fibrillation
            4119602,  # Non-rheumatic atrial fibrillation
            # MYOCARDIAL_INFARCTION codes from tutorial codelists
            312327,  # Acute myocardial infarction (main tutorial code)
            4296653,  # Acute ST segment elevation myocardial infarction
            4270024,  # Acute non-ST segment elevation myocardial infarction
            314666,  # Old myocardial infarction
            4163874,  # History of myocardial infarction
            438170,  # Acute myocardial infarction of inferior wall
        ]
        condition_concept_ids = np.random.choice(
            common_condition_concepts, size=total_conditions
        )

        # Generate dates - condition start dates must be after birth and before death (vectorized)
        condition_start_dates, condition_start_datetimes = (
            self._generate_dates_within_lifespan(
                person_ids=person_ids,
                count=total_conditions,
                min_year=2014,
                max_year=2024,
                hour_range=(0, 24),
            )
        )

        # End dates - 70% have end dates, rest are ongoing (VECTORIZED)
        has_end_date = np.random.random(total_conditions) < 0.7

        # Generate all end date durations at once
        days_durations = np.random.exponential(
            30, size=total_conditions
        )  # Average 30 days
        days_durations = np.clip(days_durations, 1, 365)  # Between 1 day and 1 year

        # Convert start dates to datetime for calculation
        condition_start_datetimes_for_calc = [
            datetime.combine(date, datetime.min.time())
            for date in condition_start_dates
        ]

        # Calculate end dates and datetimes
        condition_end_dates = []
        condition_end_datetimes = []
        end_hours = np.random.randint(0, 24, size=total_conditions)
        end_minutes = np.random.randint(0, 60, size=total_conditions)

        for i, has_end in enumerate(has_end_date):
            if has_end:
                end_dt = condition_start_datetimes_for_calc[i] + timedelta(
                    days=int(days_durations[i])
                )
                condition_end_dates.append(end_dt.date())
                condition_end_datetimes.append(
                    end_dt
                    + timedelta(hours=int(end_hours[i]), minutes=int(end_minutes[i]))
                )
            else:
                condition_end_dates.append(None)
                condition_end_datetimes.append(None)

        # Condition type concept IDs (how condition was recorded)
        condition_type_concepts = np.random.choice(
            [32020, 32817, 32810, 32840],  # EHR, Claim, Physical exam, Survey
            size=total_conditions,
            p=[0.6, 0.25, 0.1, 0.05],
        )

        # Optional fields with realistic presence rates
        stop_reasons = np.where(
            np.random.random(total_conditions) < 0.1,  # 10% have stop reason
            np.random.choice(
                ["Resolved", "Patient request", "Side effects", "No longer indicated"],
                size=total_conditions,
            ),
            None,
        )

        provider_ids = np.where(
            np.random.random(total_conditions) < 0.85,  # 85% have provider
            self._generate_person_ids(total_conditions, base=800000)[:total_conditions],
            None,
        )

        visit_occurrence_ids = np.where(
            np.random.random(total_conditions) < 0.90,  # 90% associated with visit
            self._generate_person_ids(total_conditions, base=60000000)[
                :total_conditions
            ],  # 8-digit visit IDs
            None,
        )

        visit_detail_ids = np.where(
            np.random.random(total_conditions) < 0.30,  # 30% have visit detail
            np.random.choice(
                self._get_visit_detail_ids_pool(), size=total_conditions
            ),  # Use consistent IDs
            None,
        )

        # Source values - human readable condition names
        condition_source_values = np.select(
            [
                condition_concept_ids == 201820,
                condition_concept_ids == 316866,
                condition_concept_ids == 440383,
                condition_concept_ids == 432867,
                condition_concept_ids == 321596,
                condition_concept_ids == 378253,
                condition_concept_ids == 134736,  # Back pain (updated concept ID)
                condition_concept_ids == 4170143,
                condition_concept_ids == 200219,
                # ATRIAL_FIBRILLATION conditions
                condition_concept_ids == 1569171,
                condition_concept_ids == 4232691,
                condition_concept_ids == 4154290,
                condition_concept_ids == 4232697,
                condition_concept_ids == 4119602,
                # MYOCARDIAL_INFARCTION conditions
                condition_concept_ids == 312327,  # Acute myocardial infarction
                condition_concept_ids == 4296653,
                condition_concept_ids == 4270024,
                condition_concept_ids == 314666,
                condition_concept_ids == 4163874,
                condition_concept_ids == 438170,
            ],
            [
                "Type 2 Diabetes",
                "Hypertension",
                "Depression",
                "Asthma",
                "Cough",
                "Headache",
                "Back Pain",
                "Chest Pain",
                "Pneumonia",
                # ATRIAL_FIBRILLATION labels
                "Chronic Atrial Fibrillation",
                "Permanent Atrial Fibrillation",
                "Paroxysmal Atrial Fibrillation",
                "Persistent Atrial Fibrillation",
                "Non-rheumatic Atrial Fibrillation",
                # MYOCARDIAL_INFARCTION labels
                "Acute Myocardial Infarction",  # Main tutorial MI code
                "Acute ST Elevation MI",
                "Acute Non-ST Elevation MI",
                "Old Myocardial Infarction",
                "History of Myocardial Infarction",
                "Acute Inferior MI",
            ],
            default="Other Condition",
        )

        condition_source_concept_ids = np.where(
            np.random.random(total_conditions) < 0.8,  # 80% have source concept
            condition_concept_ids,  # Same as standard concept for simplicity
            None,
        )

        # Condition status
        condition_status_source_values = np.where(
            np.random.random(total_conditions) < 0.4,  # 40% have status
            np.random.choice(
                ["Active", "Resolved", "Inactive", "Chronic"], size=total_conditions
            ),
            None,
        )

        condition_status_concept_ids = np.where(
            condition_status_source_values == "Active",
            4230359,
            np.where(
                condition_status_source_values == "Resolved",
                4230360,
                np.where(
                    condition_status_source_values == "Inactive",
                    4262691,
                    np.where(
                        condition_status_source_values == "Chronic", 4052488, None
                    ),
                ),
            ),
        )

        return pd.DataFrame(
            {
                "CONDITION_OCCURRENCE_ID": condition_occurrence_ids,
                "PERSON_ID": person_ids,
                "CONDITION_CONCEPT_ID": condition_concept_ids,
                "CONDITION_START_DATE": condition_start_dates,  # Already date objects from optimized function
                "CONDITION_START_DATETIME": condition_start_datetimes,
                "CONDITION_END_DATE": condition_end_dates,
                "CONDITION_END_DATETIME": condition_end_datetimes,
                "CONDITION_TYPE_CONCEPT_ID": condition_type_concepts,
                "STOP_REASON": stop_reasons,
                "PROVIDER_ID": provider_ids,
                "VISIT_OCCURRENCE_ID": visit_occurrence_ids,
                "VISIT_DETAIL_ID": visit_detail_ids,
                "CONDITION_SOURCE_VALUE": condition_source_values,
                "CONDITION_SOURCE_CONCEPT_ID": condition_source_concept_ids,
                "CONDITION_STATUS_SOURCE_VALUE": condition_status_source_values,
                "CONDITION_STATUS_CONCEPT_ID": condition_status_concept_ids,
            }
        )

    def _mock_procedure_occurrence_table(self) -> pd.DataFrame:
        """
        Mock the PROCEDURE_OCCURRENCE table with OMOP schema.

        Returns:
            pd.DataFrame: Mocked procedure occurrence table data
        """
        # Generate procedures for patients - use Poisson distribution for number of procedures per patient
        procedures_per_patient = np.random.poisson(
            lam=2.8, size=self.n_patients
        )  # Average 2-3 procedures per patient
        procedures_per_patient = np.clip(
            procedures_per_patient, 0, 15
        )  # Cap at 15 procedures

        total_procedures = procedures_per_patient.sum()

        # Generate procedure occurrence IDs that look realistic
        procedure_occurrence_ids = self._generate_person_ids(
            total_procedures, base=40000000
        )  # 8-digit IDs

        # Generate person IDs based on procedures per patient
        person_ids = np.repeat(self.base_patient_ids, procedures_per_patient)

        # Common procedure concept IDs (colonoscopy, mammography, blood tests, etc.)
        common_procedure_concepts = [
            4038534,  # Colonoscopy
            4037149,  # Mammography
            4267704,  # Complete blood count
            4039592,  # Electrocardiogram
            4267147,  # Blood glucose measurement
            4038863,  # CT scan of chest
            4037149,  # Chest X-ray
            4089442,  # Influenza vaccination
            4037302,  # MRI of brain
            4037640,  # Echocardiography
        ]
        procedure_concept_ids = np.random.choice(
            common_procedure_concepts, size=total_procedures
        )

        # Generate dates - procedure dates must be after birth and before death (vectorized)
        procedure_dates, procedure_datetimes = self._generate_dates_within_lifespan(
            person_ids=person_ids,
            count=total_procedures,
            min_year=2014,
            max_year=2024,
            hour_range=(6, 18),  # Business hours
        )

        # Procedure type concept IDs (how procedure was recorded)
        procedure_type_concepts = np.random.choice(
            [
                32020,
                32817,
                32810,
                32879,
            ],  # EHR, Claim, Physical exam, Procedure billing code
            size=total_procedures,
            p=[0.5, 0.35, 0.1, 0.05],
        )

        # Optional fields with realistic presence rates
        modifier_concept_ids = np.where(
            np.random.random(total_procedures) < 0.15,  # 15% have modifier
            np.random.choice(
                [4052488, 4230359, 4262691], size=total_procedures
            ),  # Some procedure modifiers
            None,
        )

        # Quantity - most procedures are quantity 1, some have higher quantities
        quantities = np.where(
            np.random.random(total_procedures) < 0.85,  # 85% have quantity 1
            1,
            np.random.choice(
                [2, 3, 4, 5], size=total_procedures, p=[0.5, 0.3, 0.15, 0.05]
            ),
        )

        provider_ids = np.where(
            np.random.random(total_procedures) < 0.90,  # 90% have provider
            self._generate_person_ids(total_procedures, base=800000)[:total_procedures],
            None,
        )

        visit_occurrence_ids = np.where(
            np.random.random(total_procedures) < 0.85,  # 85% associated with visit
            self._generate_person_ids(total_procedures, base=60000000)[
                :total_procedures
            ],
            None,
        )

        visit_detail_ids = np.where(
            np.random.random(total_procedures) < 0.25,  # 25% have visit detail
            np.random.choice(
                self._get_visit_detail_ids_pool(), size=total_procedures
            ),  # Use consistent IDs
            None,
        )

        # Source values - human readable procedure names
        procedure_source_values = np.select(
            [
                procedure_concept_ids == 4038534,
                procedure_concept_ids == 4037149,
                procedure_concept_ids == 4267704,
                procedure_concept_ids == 4039592,
                procedure_concept_ids == 4267147,
                procedure_concept_ids == 4038863,
                procedure_concept_ids == 4037149,
                procedure_concept_ids == 4089442,
                procedure_concept_ids == 4037302,
                procedure_concept_ids == 4037640,
            ],
            [
                "Colonoscopy",
                "Mammogram",
                "CBC",
                "EKG",
                "Blood glucose",
                "Chest CT",
                "Chest X-ray",
                "Flu shot",
                "Brain MRI",
                "Echo",
            ],
            default="Other Procedure",
        )

        procedure_source_concept_ids = np.where(
            np.random.random(total_procedures) < 0.75,  # 75% have source concept
            procedure_concept_ids,  # Same as standard concept for simplicity
            None,
        )

        # Modifier source values
        modifier_source_values = np.where(
            modifier_concept_ids.astype(str) != "None",
            np.random.choice(
                ["Bilateral", "Left", "Right", "Repeat"], size=total_procedures
            ),
            None,
        )

        return pd.DataFrame(
            {
                "PROCEDURE_OCCURRENCE_ID": procedure_occurrence_ids,
                "PERSON_ID": person_ids,
                "PROCEDURE_CONCEPT_ID": procedure_concept_ids,
                "PROCEDURE_DATE": procedure_dates,  # Already date objects from vectorized function
                "PROCEDURE_DATETIME": procedure_datetimes,
                "PROCEDURE_TYPE_CONCEPT_ID": procedure_type_concepts,
                "MODIFIER_CONCEPT_ID": modifier_concept_ids,
                "QUANTITY": quantities,
                "PROVIDER_ID": provider_ids,
                "VISIT_OCCURRENCE_ID": visit_occurrence_ids,
                "VISIT_DETAIL_ID": visit_detail_ids,
                "PROCEDURE_SOURCE_VALUE": procedure_source_values,
                "PROCEDURE_SOURCE_CONCEPT_ID": procedure_source_concept_ids,
                "MODIFIER_SOURCE_VALUE": modifier_source_values,
            }
        )

    def _mock_death_table(self) -> pd.DataFrame:
        """
        Mock the DEATH table with OMOP schema.
        Uses caching to ensure consistency across table generations.

        Returns:
            pd.DataFrame: Mocked death table data
        """
        # Return cached death data if it exists
        if self._death_data is not None:
            return self._death_data

        # Generate death data for the first time
        # Use the actual birth years from each person ID to ensure consistency
        birth_years = self._get_person_birth_years()
        current_year = 2024
        ages = current_year - birth_years

        # Age-stratified death probability (very simplified)
        death_probs = np.where(
            ages < 50,
            0.005,  # 0.5% for under 50
            np.where(
                ages < 70,
                0.02,  # 2% for 50-70
                np.where(ages < 80, 0.08, 0.25),  # 8% for 70-80
            ),  # 25% for 80+
        )

        has_death = np.random.random(self.n_patients) < death_probs
        deceased_patient_ids = self.base_patient_ids[has_death]
        deceased_birth_years = birth_years[has_death]
        total_deaths = len(deceased_patient_ids)

        if total_deaths == 0:
            # Return empty DataFrame with correct schema
            return pd.DataFrame(
                {
                    "PERSON_ID": [],
                    "DEATH_DATE": [],
                    "DEATH_DATETIME": [],
                    "DEATH_TYPE_CONCEPT_ID": [],
                    "CAUSE_CONCEPT_ID": [],
                    "CAUSE_SOURCE_VALUE": [],
                    "CAUSE_SOURCE_CONCEPT_ID": [],
                }
            )

        # Generate death dates

        # Calculate valid death year ranges for each deceased patient
        min_death_years = np.maximum(
            deceased_birth_years + 1, 2019
        )  # At least 2019, after birth
        max_death_years = np.full(total_deaths, 2024)  # All can die up to 2024

        # Handle edge case where min > max (very old people)
        min_death_years = np.minimum(min_death_years, max_death_years)

        # Generate random death years vectorized
        year_ranges = max_death_years - min_death_years + 1
        random_year_offsets = np.floor(
            np.random.random(total_deaths) * year_ranges
        ).astype(int)
        death_years = min_death_years + random_year_offsets

        # For vectorized date creation, use a simpler approach:
        # Generate days since a reference date (Jan 1, 2019)
        reference_date = datetime(2019, 1, 1)

        # Calculate days since reference for start and end of valid ranges
        days_since_ref_start = (death_years - 2019) * 365
        days_since_ref_end = days_since_ref_start + 364  # ~365 days per year

        # Generate random days within valid ranges
        day_ranges = days_since_ref_end - days_since_ref_start + 1
        random_day_offsets = np.floor(
            np.random.random(total_deaths) * day_ranges
        ).astype(int)
        random_days_since_ref = days_since_ref_start + random_day_offsets

        # Generate random hours and minutes (vectorized)
        random_hours = np.random.randint(0, 24, size=total_deaths)
        random_minutes = np.random.randint(0, 60, size=total_deaths)

        # Convert to actual dates using pandas for speed
        death_base_dates = pd.to_datetime(reference_date) + pd.to_timedelta(
            random_days_since_ref, unit="days"
        )
        death_datetimes_pd = (
            death_base_dates
            + pd.to_timedelta(random_hours, unit="hours")
            + pd.to_timedelta(random_minutes, unit="minutes")
        )

        # Convert to Python objects
        death_dates = [dt.date() for dt in death_base_dates]
        death_datetimes = [dt.to_pydatetime() for dt in death_datetimes_pd]

        # Death type concept IDs (how death was recorded)
        death_type_concepts = np.random.choice(
            [
                32817,
                32020,
                32879,
                32810,
            ],  # Claim, EHR, Procedure billing, Physical exam
            size=total_deaths,
            p=[0.4, 0.3, 0.2, 0.1],
        )

        # Common causes of death with OMOP concept IDs
        # Updated to include tutorial-relevant MI codes
        common_death_causes = [
            312327,  # Acute myocardial infarction (tutorial code)
            4296653,  # Acute ST segment elevation myocardial infarction
            432867,  # Malignant neoplastic disease
            316866,  # Hypertensive disorder
            440383,  # Cerebrovascular accident
            200219,  # Pneumonia
            255848,  # Diabetes mellitus
            321596,  # Chronic obstructive lung disease
            374375,  # Renal failure
            434557,  # Sepsis
            0,  # Unknown/unspecified
        ]

        cause_concept_ids = np.where(
            np.random.random(total_deaths) < 0.85,  # 85% have cause recorded
            np.random.choice(
                common_death_causes[:-1],
                size=total_deaths,  # Exclude unknown for this 85%
                p=[
                    0.20,
                    0.10,
                    0.18,
                    0.10,
                    0.10,
                    0.08,
                    0.08,
                    0.07,
                    0.05,
                    0.04,
                ],  # 10 probabilities for 10 causes
            ),
            0,  # Unknown cause
        )

        # Cause source values - human readable causes
        cause_source_values = np.select(
            [
                cause_concept_ids == 312327,  # Acute myocardial infarction
                cause_concept_ids == 4296653,  # Acute ST segment elevation MI
                cause_concept_ids == 432867,
                cause_concept_ids == 316866,
                cause_concept_ids == 440383,
                cause_concept_ids == 200219,
                cause_concept_ids == 255848,
                cause_concept_ids == 321596,
                cause_concept_ids == 374375,
                cause_concept_ids == 434557,
                cause_concept_ids == 0,
            ],
            [
                "Acute Myocardial Infarction",
                "Acute ST Elevation MI",
                "Cancer",
                "Hypertension",
                "Stroke",
                "Pneumonia",
                "Diabetes",
                "COPD",
                "Kidney Failure",
                "Sepsis",
                "Unknown",
            ],
            default="Other",
        )

        # Set unknown causes to None for source values
        cause_source_values = np.where(
            cause_concept_ids == 0, None, cause_source_values
        )

        cause_source_concept_ids = np.where(
            (cause_concept_ids != 0)
            & (
                np.random.random(total_deaths) < 0.80
            ),  # 80% of non-unknown have source concept
            cause_concept_ids,  # Same as standard concept for simplicity
            None,
        )

        death_data = pd.DataFrame(
            {
                "PERSON_ID": deceased_patient_ids,
                "DEATH_DATE": death_dates,  # Already date objects
                "DEATH_DATETIME": death_datetimes,
                "DEATH_TYPE_CONCEPT_ID": death_type_concepts,
                "CAUSE_CONCEPT_ID": cause_concept_ids,
                "CAUSE_SOURCE_VALUE": cause_source_values,
                "CAUSE_SOURCE_CONCEPT_ID": cause_source_concept_ids,
            }
        )

        # Cache the death data for consistency across table generations
        self._death_data = death_data
        return death_data

    def _mock_drug_exposure_table(self) -> pd.DataFrame:
        """
        Mock the DRUG_EXPOSURE table with OMOP schema.

        Returns:
            pd.DataFrame: Mocked drug exposure table data
        """
        # Generate drug exposures for patients - use Poisson distribution for number of drugs per patient
        drugs_per_patient = np.random.poisson(
            lam=4.2, size=self.n_patients
        )  # Average 4-5 drugs per patient
        drugs_per_patient = np.clip(drugs_per_patient, 0, 25)  # Cap at 25 drugs

        total_drugs = drugs_per_patient.sum()

        # Generate drug exposure IDs that look realistic
        drug_exposure_ids = self._generate_person_ids(
            total_drugs, base=80000000
        )  # 8-digit IDs

        # Generate person IDs based on drugs per patient
        person_ids = np.repeat(self.base_patient_ids, drugs_per_patient)

        # Common drug concept IDs (statins, ACE inhibitors, metformin, etc.)
        common_drug_concepts = [
            1539403,  # Atorvastatin
            1308216,  # Lisinopril
            1503297,  # Metformin
            1136980,  # Amlodipine
            1118084,  # Metoprolol
            19001065,  # Levothyroxine
            1124300,  # Omeprazole
            1777087,  # Simvastatin
            1386957,  # Hydrochlorothiazide
            40161532,  # Aspirin
        ]
        drug_concept_ids = np.random.choice(common_drug_concepts, size=total_drugs)

        # Generate dates - drug start dates must be after birth and before death (vectorized)
        drug_start_dates, drug_start_datetimes = self._generate_dates_within_lifespan(
            person_ids=person_ids,
            count=total_drugs,
            min_year=2019,
            max_year=2024,
            hour_range=(8, 18),  # Pharmacy hours
        )

        # End dates - 60% have end dates (acute treatments), 40% are ongoing (chronic) (VECTORIZED)
        has_end_date = np.random.random(total_drugs) < 0.6

        # Generate all end date durations at once
        days_durations = np.random.exponential(45, size=total_drugs)  # Average 45 days
        days_durations = np.clip(days_durations, 7, 365)  # Between 7 days and 1 year

        # Convert start dates to datetime for calculation
        drug_start_datetimes_for_calc = [
            datetime.combine(date, datetime.min.time()) for date in drug_start_dates
        ]

        # Pre-generate random hours/minutes for end times
        end_hours = np.random.randint(8, 18, size=total_drugs)
        end_minutes = np.random.randint(0, 60, size=total_drugs)
        verbatim_mask = (
            np.random.random(total_drugs) < 0.3
        )  # 30% have verbatim end dates

        # Calculate end dates and datetimes
        drug_end_dates = []
        drug_end_datetimes = []
        verbatim_end_dates = []

        for i, has_end in enumerate(has_end_date):
            if has_end:
                end_dt = drug_start_datetimes_for_calc[i] + timedelta(
                    days=int(days_durations[i])
                )
                drug_end_dates.append(end_dt.date())
                drug_end_datetimes.append(
                    end_dt
                    + timedelta(hours=int(end_hours[i]), minutes=int(end_minutes[i]))
                )
                # 30% of drugs with end dates have verbatim end dates
                if verbatim_mask[i]:
                    verbatim_end_dates.append(end_dt.date())
                else:
                    verbatim_end_dates.append(None)
            else:
                drug_end_dates.append(None)
                drug_end_datetimes.append(None)
                verbatim_end_dates.append(None)

        # Drug type concept IDs (how drug was prescribed/dispensed)
        drug_type_concepts = np.random.choice(
            [
                32817,
                32020,
                32879,
                581373,
            ],  # Claim, EHR, Procedure billing, Prescription written
            size=total_drugs,
            p=[0.5, 0.3, 0.1, 0.1],
        )

        # Optional fields with realistic presence rates
        stop_reasons = np.where(
            (np.array(drug_end_dates) != None)
            & (
                np.random.random(total_drugs) < 0.15
            ),  # 15% of ended drugs have stop reason
            np.random.choice(
                ["Completed course", "Side effects", "Ineffective", "Patient request"],
                size=total_drugs,
            ),
            None,
        )

        # Refills - most prescriptions have 0-5 refills
        refills = np.where(
            np.random.random(total_drugs) < 0.80,  # 80% have refill info
            np.random.choice(
                [0, 1, 2, 3, 5], size=total_drugs, p=[0.3, 0.25, 0.2, 0.15, 0.1]
            ),
            None,
        )

        # Quantity - realistic quantities for different drug types
        quantities = np.where(
            np.random.random(total_drugs) < 0.85,  # 85% have quantity
            np.random.choice(
                [30.0, 60.0, 90.0, 100.0, 120.0],
                size=total_drugs,
                p=[0.4, 0.25, 0.2, 0.1, 0.05],
            ),  # Common quantities
            None,
        )

        # Days supply
        days_supply = np.where(
            np.random.random(total_drugs) < 0.80,  # 80% have days supply
            np.random.choice([30, 60, 90], size=total_drugs, p=[0.6, 0.25, 0.15]),
            None,
        )

        # SIG (directions for use)
        sigs = np.where(
            np.random.random(total_drugs) < 0.70,  # 70% have sig
            np.random.choice(
                [
                    "Take 1 tablet by mouth daily",
                    "Take 1 tablet twice daily",
                    "Take 1 tablet as needed",
                    "Apply topically twice daily",
                    "Take 2 tablets daily",
                ],
                size=total_drugs,
                p=[0.4, 0.25, 0.15, 0.1, 0.1],
            ),
            None,
        )

        # Route concept IDs
        route_concept_ids = np.where(
            np.random.random(total_drugs) < 0.75,  # 75% have route
            np.random.choice(
                [4132161, 4161906, 4262099],
                size=total_drugs,  # Oral, Topical, Injection
                p=[0.85, 0.1, 0.05],
            ),
            None,
        )

        # Lot numbers - only small percentage have lot numbers (VECTORIZED)
        lot_mask = np.random.random(total_drugs) < 0.05  # 5% have lot numbers
        lot_random_nums = np.random.randint(100000, 999999, size=total_drugs)
        lot_numbers = np.where(
            lot_mask,
            [f"LOT{num}" for num in lot_random_nums],
            None,
        )

        provider_ids = np.where(
            np.random.random(total_drugs) < 0.85,  # 85% have provider
            self._generate_person_ids(total_drugs, base=800000)[:total_drugs],
            None,
        )

        visit_occurrence_ids = np.where(
            np.random.random(total_drugs) < 0.70,  # 70% associated with visit
            self._generate_person_ids(total_drugs, base=60000000)[:total_drugs],
            None,
        )

        visit_detail_ids = np.where(
            np.random.random(total_drugs) < 0.20,  # 20% have visit detail
            np.random.choice(
                self._get_visit_detail_ids_pool(), size=total_drugs
            ),  # Use consistent IDs
            None,
        )

        # Source values - human readable drug names
        drug_source_values = np.select(
            [
                drug_concept_ids == 1539403,
                drug_concept_ids == 1308216,
                drug_concept_ids == 1503297,
                drug_concept_ids == 1136980,
                drug_concept_ids == 1118084,
                drug_concept_ids == 19001065,
                drug_concept_ids == 1124300,
                drug_concept_ids == 1777087,
                drug_concept_ids == 1386957,
                drug_concept_ids == 40161532,
            ],
            [
                "Atorvastatin 20mg",
                "Lisinopril 10mg",
                "Metformin 500mg",
                "Amlodipine 5mg",
                "Metoprolol 50mg",
                "Levothyroxine 50mcg",
                "Omeprazole 20mg",
                "Simvastatin 20mg",
                "HCTZ 25mg",
                "Aspirin 81mg",
            ],
            default="Other Medication",
        )

        drug_source_concept_ids = np.where(
            np.random.random(total_drugs) < 0.70,  # 70% have source concept
            drug_concept_ids,  # Same as standard concept for simplicity
            None,
        )

        # Route source values
        route_source_values = np.where(
            route_concept_ids.astype(str) != "None",
            np.select(
                [
                    route_concept_ids == 4132161,
                    route_concept_ids == 4161906,
                    route_concept_ids == 4262099,
                ],
                ["PO", "Topical", "IM"],
                default="Other",
            ),
            None,
        )

        # Dose unit source values
        dose_unit_source_values = np.where(
            np.random.random(total_drugs) < 0.60,  # 60% have dose unit
            np.random.choice(
                ["mg", "mcg", "mL", "units"], size=total_drugs, p=[0.7, 0.15, 0.1, 0.05]
            ),
            None,
        )

        return pd.DataFrame(
            {
                "DRUG_EXPOSURE_ID": drug_exposure_ids,
                "PERSON_ID": person_ids,
                "DRUG_CONCEPT_ID": drug_concept_ids,
                "DRUG_EXPOSURE_START_DATE": drug_start_dates,  # Already date objects from optimized function
                "DRUG_EXPOSURE_START_DATETIME": drug_start_datetimes,
                "DRUG_EXPOSURE_END_DATE": drug_end_dates,
                "DRUG_EXPOSURE_END_DATETIME": drug_end_datetimes,
                "VERBATIM_END_DATE": verbatim_end_dates,
                "DRUG_TYPE_CONCEPT_ID": drug_type_concepts,
                "STOP_REASON": stop_reasons,
                "REFILLS": refills,
                "QUANTITY": quantities,
                "DAYS_SUPPLY": days_supply,
                "SIG": sigs,
                "ROUTE_CONCEPT_ID": route_concept_ids,
                "LOT_NUMBER": lot_numbers,
                "PROVIDER_ID": provider_ids,
                "VISIT_OCCURRENCE_ID": visit_occurrence_ids,
                "VISIT_DETAIL_ID": visit_detail_ids,
                "DRUG_SOURCE_VALUE": drug_source_values,
                "DRUG_SOURCE_CONCEPT_ID": drug_source_concept_ids,
                "ROUTE_SOURCE_VALUE": route_source_values,
                "DOSE_UNIT_SOURCE_VALUE": dose_unit_source_values,
            }
        )

    def _get_visit_detail_ids_pool(self) -> np.ndarray:
        """
        Generate a pool of visit detail IDs that can be consistently referenced across tables.

        Returns:
            np.ndarray: Array of visit detail IDs
        """
        if self._visit_detail_ids_pool is None:
            # Generate enough visit details to handle Poisson distribution
            # Use 3x patients to ensure we have enough IDs for the Poisson distribution
            n_visit_details = int(self.n_patients * 3)
            self._visit_detail_ids_pool = self._generate_person_ids(
                n_visit_details, base=70000000
            )
        return self._visit_detail_ids_pool

    def _get_visit_occurrence_ids_pool(self) -> np.ndarray:
        """
        Generate a pool of visit occurrence IDs that can be consistently referenced across tables.

        Returns:
            np.ndarray: Array of visit occurrence IDs
        """
        if self._visit_occurrence_ids_pool is None:
            # Generate enough visit occurrences to handle realistic visit patterns
            # Use 2x patients to ensure we have enough IDs for various visit types
            n_visit_occurrences = int(self.n_patients * 2)
            self._visit_occurrence_ids_pool = self._generate_person_ids(
                n_visit_occurrences, base=60000000
            )
        return self._visit_occurrence_ids_pool

    def _get_person_birth_years(self) -> np.ndarray:
        """
        Generate birth years for all patients that can be consistently referenced across tables.

        Returns:
            np.ndarray: Array of birth years
        """
        if self._person_birth_years is None:
            # Generate birth years with realistic distribution
            self._person_birth_years = np.random.choice(
                np.arange(1930, 2011),
                size=self.n_patients,
                p=self._generate_birth_year_probs(),
            )
        return self._person_birth_years

    def _mock_visit_occurrence_table(self) -> pd.DataFrame:
        """
        Mock the VISIT_OCCURRENCE table with OMOP schema.

        Returns:
            pd.DataFrame: Mocked visit occurrence table data
        """
        # Generate visit occurrences for patients - use Poisson distribution for number of visits per patient
        visits_per_patient = np.random.poisson(
            lam=1.8, size=self.n_patients
        )  # Average 1.8 visits per patient
        visits_per_patient = np.clip(visits_per_patient, 0, 10)  # Cap at 10 visits

        total_visits = visits_per_patient.sum()

        if total_visits == 0:
            # Return empty DataFrame with correct schema
            return pd.DataFrame(
                {
                    "VISIT_OCCURRENCE_ID": [],
                    "PERSON_ID": [],
                    "VISIT_CONCEPT_ID": [],
                    "VISIT_START_DATE": [],
                    "VISIT_START_DATETIME": [],
                    "VISIT_END_DATE": [],
                    "VISIT_END_DATETIME": [],
                    "VISIT_TYPE_CONCEPT_ID": [],
                    "PROVIDER_ID": [],
                    "CARE_SITE_ID": [],
                    "VISIT_SOURCE_VALUE": [],
                    "VISIT_SOURCE_CONCEPT_ID": [],
                    "ADMITTING_SOURCE_CONCEPT_ID": [],
                    "ADMITTING_SOURCE_VALUE": [],
                    "DISCHARGE_TO_CONCEPT_ID": [],
                    "DISCHARGE_TO_SOURCE_VALUE": [],
                    "PRECEDING_VISIT_OCCURRENCE_ID": [],
                }
            )

        # Use the pre-generated visit occurrence IDs
        visit_occurrence_ids = self._get_visit_occurrence_ids_pool()[:total_visits]

        # Generate person IDs based on visits per patient
        person_ids = np.repeat(self.base_patient_ids, visits_per_patient)

        # Visit concept IDs (different types of visits)
        visit_concepts = np.random.choice(
            [
                9202,  # Outpatient Visit
                9201,  # Inpatient Visit
                9203,  # Emergency Room Visit
                581478,  # Emergency Room and Inpatient Visit
                32037,  # Observation Visit
            ],
            size=total_visits,
            p=[0.65, 0.15, 0.12, 0.05, 0.03],
        )

        # Generate dates - visit start dates must be after birth and before death (vectorized)
        visit_start_dates, visit_start_datetimes = self._generate_dates_within_lifespan(
            person_ids=person_ids,
            count=total_visits,
            min_year=2021,
            max_year=2024,
            hour_range=(0, 24),
        )

        # End dates - all visits have end dates (VECTORIZED APPROACH)
        # Generate duration hours based on visit type using vectorized operations
        duration_hours = np.zeros(total_visits)

        # Outpatient visits (same day) - average 2 hours
        outpatient_mask = visit_concepts == 9202
        outpatient_durations = np.random.exponential(2, size=np.sum(outpatient_mask))
        duration_hours[outpatient_mask] = np.clip(outpatient_durations, 0.5, 8)

        # Inpatient visits - average 4 days (96 hours)
        inpatient_mask = np.isin(visit_concepts, [9201, 581478])
        inpatient_durations = np.random.exponential(96, size=np.sum(inpatient_mask))
        duration_hours[inpatient_mask] = np.clip(inpatient_durations, 12, 720)

        # ER visits - average 6 hours
        er_mask = visit_concepts == 9203
        er_durations = np.random.exponential(6, size=np.sum(er_mask))
        duration_hours[er_mask] = np.clip(er_durations, 1, 24)

        # Other visits (observation) - average 24 hours
        other_mask = ~(outpatient_mask | inpatient_mask | er_mask)
        other_durations = np.random.exponential(24, size=np.sum(other_mask))
        duration_hours[other_mask] = np.clip(other_durations, 4, 72)

        # Calculate end datetimes vectorized - ensure proper datetime handling
        visit_end_datetimes = []
        for start_dt, hours in zip(visit_start_datetimes, duration_hours):
            end_dt = start_dt + timedelta(hours=float(hours))
            visit_end_datetimes.append(end_dt)
        visit_end_dates = [dt.date() for dt in visit_end_datetimes]

        # Visit type concept IDs (how visit was recorded)
        visit_type_concepts = np.random.choice(
            [32817, 32020, 32810],  # Claim, EHR, Physical exam
            size=total_visits,
            p=[0.6, 0.35, 0.05],
        )

        # Optional fields with realistic presence rates
        provider_mask = np.random.random(total_visits) < 0.90  # 90% have provider
        provider_values = self._generate_person_ids(total_visits, base=800000)
        provider_ids = np.where(provider_mask, provider_values, None)

        care_site_mask = np.random.random(total_visits) < 0.85  # 85% have care site
        care_site_values = self._generate_person_ids(total_visits, base=300000)
        care_site_ids = np.where(care_site_mask, care_site_values, None)

        # Admitting source - only for inpatient-like visits
        admitting_mask = (visit_concepts != 9202) & (
            np.random.random(total_visits) < 0.70
        )  # 70% of non-outpatient have admitting source
        admitting_values = np.random.choice(
            [8844, 8870, 8863], size=total_visits, p=[0.4, 0.4, 0.2]
        )  # Emergency Room, Physician Referral, Transfer
        admitting_source_concept_ids = np.where(admitting_mask, admitting_values, None)

        # Discharge to
        discharge_mask = (
            np.random.random(total_visits) < 0.80
        )  # 80% have discharge destination
        discharge_values = np.random.choice(
            [8536, 8844, 8717], size=total_visits, p=[0.7, 0.15, 0.15]
        )  # Home, Emergency Room, Skilled Nursing
        discharge_to_concept_ids = np.where(discharge_mask, discharge_values, None)

        # Preceding visit occurrence - 15% have preceding visit
        preceding_mask = np.random.random(total_visits) < 0.15
        preceding_values = np.random.choice(visit_occurrence_ids, size=total_visits)
        preceding_visit_occurrence_ids = np.where(
            preceding_mask, preceding_values, None
        )

        # Source values
        visit_source_values = np.select(
            [
                visit_concepts == 9202,
                visit_concepts == 9201,
                visit_concepts == 9203,
                visit_concepts == 581478,
                visit_concepts == 32037,
            ],
            [
                "Outpatient Visit",
                "Inpatient Visit",
                "Emergency Room Visit",
                "Emergency Room and Inpatient Visit",
                "Observation Visit",
            ],
            default="Other Visit",
        )

        visit_source_concept_ids = np.where(
            np.random.random(total_visits) < 0.75,  # 75% have source concept
            visit_concepts,
            None,
        )

        # Admitting/discharge source values
        admitting_source_values = np.where(
            admitting_source_concept_ids != None,
            np.select(
                [
                    admitting_source_concept_ids == 8844,
                    admitting_source_concept_ids == 8870,
                    admitting_source_concept_ids == 8863,
                ],
                ["Emergency Room", "Physician Referral", "Transfer"],
                default="Other",
            ),
            None,
        )

        discharge_to_source_values = np.where(
            discharge_to_concept_ids != None,
            np.select(
                [
                    discharge_to_concept_ids == 8536,
                    discharge_to_concept_ids == 8844,
                    discharge_to_concept_ids == 8717,
                ],
                ["Home", "Emergency Room", "Skilled Nursing"],
                default="Other",
            ),
            None,
        )

        return pd.DataFrame(
            {
                "VISIT_OCCURRENCE_ID": visit_occurrence_ids,
                "PERSON_ID": person_ids,
                "VISIT_CONCEPT_ID": visit_concepts,
                "VISIT_START_DATE": visit_start_dates,  # Already date objects from optimized function
                "VISIT_START_DATETIME": visit_start_datetimes,
                "VISIT_END_DATE": visit_end_dates,
                "VISIT_END_DATETIME": visit_end_datetimes,
                "VISIT_TYPE_CONCEPT_ID": visit_type_concepts,
                "PROVIDER_ID": provider_ids,
                "CARE_SITE_ID": care_site_ids,
                "VISIT_SOURCE_VALUE": visit_source_values,
                "VISIT_SOURCE_CONCEPT_ID": visit_source_concept_ids,
                "ADMITTING_SOURCE_CONCEPT_ID": admitting_source_concept_ids,
                "ADMITTING_SOURCE_VALUE": admitting_source_values,
                "DISCHARGE_TO_CONCEPT_ID": discharge_to_concept_ids,
                "DISCHARGE_TO_SOURCE_VALUE": discharge_to_source_values,
                "PRECEDING_VISIT_OCCURRENCE_ID": preceding_visit_occurrence_ids,
            }
        )

    def _mock_visit_detail_table(self) -> pd.DataFrame:
        """
        Mock the VISIT_DETAIL table with OMOP schema.

        Returns:
            pd.DataFrame: Mocked visit detail table data
        """
        # Generate visit details - some patients have multiple visit details, some have none
        visit_details_per_patient = np.random.poisson(
            lam=1.5, size=self.n_patients
        )  # Average 1.5 per patient
        visit_details_per_patient = np.clip(
            visit_details_per_patient, 0, 8
        )  # Cap at 8 visit details

        total_visit_details = visit_details_per_patient.sum()

        if total_visit_details == 0:
            # Return empty DataFrame with correct schema
            return pd.DataFrame(
                {
                    "VISIT_DETAIL_ID": [],
                    "PERSON_ID": [],
                    "VISIT_DETAIL_CONCEPT_ID": [],
                    "VISIT_DETAIL_START_DATE": [],
                    "VISIT_DETAIL_START_DATETIME": [],
                    "VISIT_DETAIL_END_DATE": [],
                    "VISIT_DETAIL_END_DATETIME": [],
                    "VISIT_DETAIL_TYPE_CONCEPT_ID": [],
                    "PROVIDER_ID": [],
                    "CARE_SITE_ID": [],
                    "ADMITTING_SOURCE_CONCEPT_ID": [],
                    "DISCHARGE_TO_CONCEPT_ID": [],
                    "PRECEDING_VISIT_DETAIL_ID": [],
                    "VISIT_DETAIL_SOURCE_VALUE": [],
                    "VISIT_DETAIL_SOURCE_CONCEPT_ID": [],
                    "ADMITTING_SOURCE_VALUE": [],
                    "DISCHARGE_TO_SOURCE_VALUE": [],
                    "VISIT_DETAIL_PARENT_ID": [],
                    "VISIT_OCCURRENCE_ID": [],
                }
            )

        # Use the pre-generated visit detail IDs
        visit_detail_ids = self._get_visit_detail_ids_pool()[:total_visit_details]

        # Generate person IDs based on visit details per patient
        person_ids = np.repeat(self.base_patient_ids, visit_details_per_patient)

        # Visit detail concept IDs (different types of visit details)
        visit_detail_concepts = np.random.choice(
            [
                581476,
                581477,
                32037,
            ],  # Emergency Room, Intensive Care Unit, Emergency Room and Inpatient
            size=total_visit_details,
            p=[0.6, 0.25, 0.15],
        )

        # Generate dates - visit detail dates over last 3 years (VECTORIZED)
        start_date = datetime(2021, 1, 1)
        end_date = datetime(2024, 12, 31)
        date_range = (end_date - start_date).days

        # Generate all random days at once (vectorized)
        random_days = np.random.uniform(0, date_range, size=total_visit_details).astype(
            int
        )
        visit_detail_start_dates = [
            start_date + timedelta(days=int(day)) for day in random_days
        ]

        # Generate random hours and minutes vectorized
        random_hours = np.random.randint(0, 24, size=total_visit_details)
        random_minutes = np.random.randint(0, 60, size=total_visit_details)

        # Create start datetimes vectorized
        visit_detail_start_datetimes = [
            dt + timedelta(hours=int(h), minutes=int(m))
            for dt, h, m in zip(visit_detail_start_dates, random_hours, random_minutes)
        ]

        # End dates - all visit details have end dates (VECTORIZED APPROACH)
        # Generate duration hours based on visit detail type using vectorized operations
        duration_hours = np.zeros(total_visit_details)

        # ER visits - average 4 hours
        er_mask = visit_detail_concepts == 581476
        er_durations = np.random.exponential(4, size=np.sum(er_mask))
        duration_hours[er_mask] = np.clip(er_durations, 1, 24)

        # ICU visits - average 3 days (72 hours)
        icu_mask = visit_detail_concepts == 581477
        icu_durations = np.random.exponential(72, size=np.sum(icu_mask))
        duration_hours[icu_mask] = np.clip(icu_durations, 6, 720)

        # Other visits - average 12 hours
        other_mask = ~(er_mask | icu_mask)
        other_durations = np.random.exponential(12, size=np.sum(other_mask))
        duration_hours[other_mask] = np.clip(other_durations, 2, 168)

        # Calculate end datetimes vectorized
        visit_detail_end_datetimes = [
            start_dt + timedelta(hours=float(duration))
            for start_dt, duration in zip(visit_detail_start_datetimes, duration_hours)
        ]
        visit_detail_end_dates = [dt.date() for dt in visit_detail_end_datetimes]

        # Visit detail type concept IDs (how visit detail was recorded)
        visit_detail_type_concepts = np.random.choice(
            [32817, 32020, 32810],  # Claim, EHR, Physical exam
            size=total_visit_details,
            p=[0.6, 0.35, 0.05],
        )

        # Optional fields with realistic presence rates
        provider_mask = (
            np.random.random(total_visit_details) < 0.90
        )  # 90% have provider
        provider_values = self._generate_person_ids(total_visit_details, base=800000)
        provider_ids = np.where(provider_mask, provider_values, None)

        care_site_mask = (
            np.random.random(total_visit_details) < 0.85
        )  # 85% have care site
        care_site_values = self._generate_person_ids(total_visit_details, base=300000)
        care_site_ids = np.where(care_site_mask, care_site_values, None)

        # Admitting source - only for inpatient-like visits
        admitting_mask = (visit_detail_concepts != 581476) & (
            np.random.random(total_visit_details) < 0.70
        )  # 70% of non-ER have admitting source
        admitting_values = np.random.choice(
            [8844, 8870, 8863], size=total_visit_details, p=[0.4, 0.4, 0.2]
        )  # Emergency Room, Physician Referral, Transfer
        admitting_source_concept_ids = np.where(admitting_mask, admitting_values, None)

        # Discharge to
        discharge_mask = (
            np.random.random(total_visit_details) < 0.80
        )  # 80% have discharge destination
        discharge_values = np.random.choice(
            [8536, 8844, 8717], size=total_visit_details, p=[0.7, 0.15, 0.15]
        )  # Home, Emergency Room, Skilled Nursing
        discharge_to_concept_ids = np.where(discharge_mask, discharge_values, None)

        # Preceding visit detail - 20% have preceding visit detail
        preceding_mask = np.random.random(total_visit_details) < 0.20
        preceding_values = np.random.choice(
            visit_detail_ids, size=total_visit_details
        )  # Reference other visit details
        preceding_visit_detail_ids = np.where(preceding_mask, preceding_values, None)

        # Source values
        visit_detail_source_values = np.select(
            [
                visit_detail_concepts == 581476,
                visit_detail_concepts == 581477,
                visit_detail_concepts == 32037,
            ],
            ["Emergency Room", "Intensive Care Unit", "Emergency and Inpatient"],
            default="Other Visit Detail",
        )

        visit_detail_source_concept_ids = np.where(
            np.random.random(total_visit_details) < 0.75,  # 75% have source concept
            visit_detail_concepts,
            None,
        )

        # Admitting/discharge source values
        admitting_source_values = np.where(
            admitting_source_concept_ids != None,
            np.select(
                [
                    admitting_source_concept_ids == 8844,
                    admitting_source_concept_ids == 8870,
                    admitting_source_concept_ids == 8863,
                ],
                ["Emergency Room", "Physician Referral", "Transfer"],
                default="Other",
            ),
            None,
        )

        discharge_to_source_values = np.where(
            discharge_to_concept_ids != None,
            np.select(
                [
                    discharge_to_concept_ids == 8536,
                    discharge_to_concept_ids == 8844,
                    discharge_to_concept_ids == 8717,
                ],
                ["Home", "Emergency Room", "Skilled Nursing"],
                default="Other",
            ),
            None,
        )

        # Parent visit detail - 30% have parent (hierarchical relationship)
        parent_mask = np.random.random(total_visit_details) < 0.30
        parent_values = np.random.choice(visit_detail_ids, size=total_visit_details)
        visit_detail_parent_ids = np.where(parent_mask, parent_values, None)

        # Visit occurrence IDs - all visit details should be associated with visit occurrences
        # Use the visit occurrence pool to ensure foreign key consistency
        visit_occurrence_ids = np.random.choice(
            self._get_visit_occurrence_ids_pool(), size=total_visit_details
        )

        return pd.DataFrame(
            {
                "VISIT_DETAIL_ID": visit_detail_ids,
                "PERSON_ID": person_ids,
                "VISIT_DETAIL_CONCEPT_ID": visit_detail_concepts,
                "VISIT_DETAIL_START_DATE": [
                    dt.date() for dt in visit_detail_start_dates
                ],
                "VISIT_DETAIL_START_DATETIME": visit_detail_start_datetimes,
                "VISIT_DETAIL_END_DATE": visit_detail_end_dates,
                "VISIT_DETAIL_END_DATETIME": visit_detail_end_datetimes,
                "VISIT_DETAIL_TYPE_CONCEPT_ID": visit_detail_type_concepts,
                "PROVIDER_ID": provider_ids,
                "CARE_SITE_ID": care_site_ids,
                "ADMITTING_SOURCE_CONCEPT_ID": admitting_source_concept_ids,
                "DISCHARGE_TO_CONCEPT_ID": discharge_to_concept_ids,
                "PRECEDING_VISIT_DETAIL_ID": preceding_visit_detail_ids,
                "VISIT_DETAIL_SOURCE_VALUE": visit_detail_source_values,
                "VISIT_DETAIL_SOURCE_CONCEPT_ID": visit_detail_source_concept_ids,
                "ADMITTING_SOURCE_VALUE": admitting_source_values,
                "DISCHARGE_TO_SOURCE_VALUE": discharge_to_source_values,
                "VISIT_DETAIL_PARENT_ID": visit_detail_parent_ids,
                "VISIT_OCCURRENCE_ID": visit_occurrence_ids,
            }
        )

    def _mock_observation_table(self) -> pd.DataFrame:
        """
        Mock the OBSERVATION table with OMOP schema.

        Returns:
            pd.DataFrame: Mocked observation table data
        """
        # Generate observations for patients - use Poisson distribution for number of observations per patient
        observations_per_patient = np.random.poisson(
            lam=6.5, size=self.n_patients
        )  # Average 6-7 observations per patient
        observations_per_patient = np.clip(
            observations_per_patient, 0, 30
        )  # Cap at 30 observations

        total_observations = observations_per_patient.sum()

        # Generate observation IDs that look realistic
        observation_ids = self._generate_person_ids(
            total_observations, base=90000000
        )  # 8-digit IDs

        # Generate person IDs based on observations per patient
        person_ids = np.repeat(self.base_patient_ids, observations_per_patient)

        # Common observation concept IDs (vital signs, lab values, survey responses, etc.)
        observation_concepts = [
            3025315,  # Body weight
            3013762,  # Body height
            3004249,  # Blood pressure systolic
            3012888,  # Blood pressure diastolic
            3027018,  # Heart rate
            3020891,  # Body temperature
            3024171,  # Respiratory rate
            3013940,  # BMI
            4083643,  # Smoking status
            4139618,  # Pain severity (0-10 scale)
        ]
        observation_concept_ids = np.random.choice(
            observation_concepts, size=total_observations
        )

        # Generate dates - observation dates over last 5 years (VECTORIZED)
        start_date = datetime(2019, 1, 1)
        end_date = datetime(2024, 12, 31)
        date_range = (end_date - start_date).days

        # Generate all random days at once (vectorized)
        random_days = np.random.uniform(0, date_range, size=total_observations).astype(
            int
        )
        observation_dates = [
            start_date + timedelta(days=int(day)) for day in random_days
        ]

        # Generate random hours and minutes vectorized
        random_hours = np.random.randint(6, 20, size=total_observations)
        random_minutes = np.random.randint(0, 60, size=total_observations)

        # Create datetimes vectorized
        observation_datetimes = [
            dt + timedelta(hours=int(h), minutes=int(m))  # During clinic hours
            for dt, h, m in zip(observation_dates, random_hours, random_minutes)
        ]

        # Observation type concept IDs (how observation was recorded)
        observation_type_concepts = np.random.choice(
            [
                32020,
                32817,
                32810,
                44818701,
            ],  # EHR, Claim, Physical exam, Patient reported
            size=total_observations,
            p=[0.5, 0.2, 0.2, 0.1],
        )

        # Generate values based on observation type - this is the complex part!
        value_as_numbers = []
        value_as_strings = []
        value_as_concept_ids = []
        unit_concept_ids = []
        unit_source_values = []

        for i, concept_id in enumerate(observation_concept_ids):
            if concept_id == 3025315:  # Body weight
                weight = np.random.normal(75, 15)  # kg, mean 75kg, std 15kg
                weight = max(30, min(weight, 200))  # Reasonable bounds
                value_as_numbers.append(weight)
                value_as_strings.append(None)
                value_as_concept_ids.append(None)
                unit_concept_ids.append(9529)  # kilogram
                unit_source_values.append("kg")

            elif concept_id == 3013762:  # Body height
                height = np.random.normal(170, 10)  # cm, mean 170cm, std 10cm
                height = max(140, min(height, 220))  # Reasonable bounds
                value_as_numbers.append(height)
                value_as_strings.append(None)
                value_as_concept_ids.append(None)
                unit_concept_ids.append(8582)  # centimeter
                unit_source_values.append("cm")

            elif concept_id == 3004249:  # Systolic BP
                systolic = np.random.normal(130, 20)  # mmHg
                systolic = max(80, min(systolic, 200))
                value_as_numbers.append(systolic)
                value_as_strings.append(None)
                value_as_concept_ids.append(None)
                unit_concept_ids.append(8876)  # mmHg
                unit_source_values.append("mmHg")

            elif concept_id == 3012888:  # Diastolic BP
                diastolic = np.random.normal(80, 15)  # mmHg
                diastolic = max(50, min(diastolic, 120))
                value_as_numbers.append(diastolic)
                value_as_strings.append(None)
                value_as_concept_ids.append(None)
                unit_concept_ids.append(8876)  # mmHg
                unit_source_values.append("mmHg")

            elif concept_id == 3027018:  # Heart rate
                hr = np.random.normal(75, 15)  # bpm
                hr = max(40, min(hr, 150))
                value_as_numbers.append(hr)
                value_as_strings.append(None)
                value_as_concept_ids.append(None)
                unit_concept_ids.append(8541)  # per minute
                unit_source_values.append("bpm")

            elif concept_id == 3020891:  # Body temperature
                temp = np.random.normal(98.6, 1.5)  # Fahrenheit
                temp = max(95, min(temp, 105))
                value_as_numbers.append(temp)
                value_as_strings.append(None)
                value_as_concept_ids.append(None)
                unit_concept_ids.append(586323)  # degree Fahrenheit
                unit_source_values.append("°F")

            elif concept_id == 3024171:  # Respiratory rate
                rr = np.random.normal(16, 4)  # breaths per minute
                rr = max(8, min(rr, 40))
                value_as_numbers.append(rr)
                value_as_strings.append(None)
                value_as_concept_ids.append(None)
                unit_concept_ids.append(8541)  # per minute
                unit_source_values.append("breaths/min")

            elif concept_id == 3013940:  # BMI
                bmi = np.random.normal(26, 5)  # kg/m2
                bmi = max(15, min(bmi, 50))
                value_as_numbers.append(bmi)
                value_as_strings.append(None)
                value_as_concept_ids.append(None)
                unit_concept_ids.append(9531)  # kg/m2
                unit_source_values.append("kg/m²")

            elif concept_id == 4083643:  # Smoking status - categorical
                smoking_concepts = [
                    45879404,
                    45883458,
                    45884037,
                ]  # Current, Former, Never
                smoking_strings = ["Current smoker", "Former smoker", "Never smoker"]
                choice = np.random.choice([0, 1, 2], p=[0.15, 0.25, 0.60])
                value_as_numbers.append(None)
                value_as_strings.append(smoking_strings[choice])
                value_as_concept_ids.append(smoking_concepts[choice])
                unit_concept_ids.append(None)
                unit_source_values.append(None)

            elif concept_id == 4139618:  # Pain severity (0-10 scale)
                pain = np.random.choice(
                    range(11),
                    p=[0.3, 0.15, 0.15, 0.1, 0.1, 0.05, 0.05, 0.03, 0.03, 0.02, 0.02],
                )
                value_as_numbers.append(float(pain))
                value_as_strings.append(f"{pain}/10")
                value_as_concept_ids.append(None)
                unit_concept_ids.append(None)  # Scale has no unit
                unit_source_values.append("scale")

            else:  # Default case
                value_as_numbers.append(None)
                value_as_strings.append("Other observation")
                value_as_concept_ids.append(None)
                unit_concept_ids.append(None)
                unit_source_values.append(None)

        # Optional fields with realistic presence rates
        qualifier_concept_ids = np.where(
            np.random.random(total_observations) < 0.10,  # 10% have qualifiers
            np.random.choice(
                [4124457, 4124458], size=total_observations
            ),  # Normal, Abnormal
            None,
        )

        provider_ids = np.where(
            np.random.random(total_observations) < 0.85,  # 85% have provider
            self._generate_person_ids(total_observations, base=800000)[
                :total_observations
            ],
            None,
        )

        visit_occurrence_ids = np.where(
            np.random.random(total_observations) < 0.80,  # 80% associated with visit
            self._generate_person_ids(total_observations, base=60000000)[
                :total_observations
            ],
            None,
        )

        visit_detail_ids = np.where(
            np.random.random(total_observations) < 0.25,  # 25% have visit detail
            np.random.choice(
                self._get_visit_detail_ids_pool(), size=total_observations
            ),  # Use consistent IDs
            None,
        )

        # Source values - human readable observation names
        observation_source_values = np.select(
            [
                observation_concept_ids == 3025315,
                observation_concept_ids == 3013762,
                observation_concept_ids == 3004249,
                observation_concept_ids == 3012888,
                observation_concept_ids == 3027018,
                observation_concept_ids == 3020891,
                observation_concept_ids == 3024171,
                observation_concept_ids == 3013940,
                observation_concept_ids == 4083643,
                observation_concept_ids == 4139618,
            ],
            [
                "Weight",
                "Height",
                "Systolic BP",
                "Diastolic BP",
                "Heart Rate",
                "Temperature",
                "Respiratory Rate",
                "BMI",
                "Smoking Status",
                "Pain Score",
            ],
            default="Other Observation",
        )

        observation_source_concept_ids = np.where(
            np.random.random(total_observations) < 0.75,  # 75% have source concept
            observation_concept_ids,  # Same as standard concept for simplicity
            None,
        )

        # Qualifier source values
        qualifier_source_values = np.where(
            qualifier_concept_ids.astype(str) != "None",
            np.select(
                [qualifier_concept_ids == 4124457, qualifier_concept_ids == 4124458],
                ["Normal", "Abnormal"],
                default="Other",
            ),
            None,
        )

        return pd.DataFrame(
            {
                "OBSERVATION_ID": observation_ids,
                "PERSON_ID": person_ids,
                "OBSERVATION_CONCEPT_ID": observation_concept_ids,
                "OBSERVATION_DATE": [dt.date() for dt in observation_dates],
                "OBSERVATION_DATETIME": observation_datetimes,
                "OBSERVATION_TYPE_CONCEPT_ID": observation_type_concepts,
                "VALUE_AS_NUMBER": value_as_numbers,
                "VALUE_AS_STRING": value_as_strings,
                "VALUE_AS_CONCEPT_ID": value_as_concept_ids,
                "QUALIFIER_CONCEPT_ID": qualifier_concept_ids,
                "UNIT_CONCEPT_ID": unit_concept_ids,
                "PROVIDER_ID": provider_ids,
                "VISIT_OCCURRENCE_ID": visit_occurrence_ids,
                "VISIT_DETAIL_ID": visit_detail_ids,
                "OBSERVATION_SOURCE_VALUE": observation_source_values,
                "OBSERVATION_SOURCE_CONCEPT_ID": observation_source_concept_ids,
                "UNIT_SOURCE_VALUE": unit_source_values,
                "QUALIFIER_SOURCE_VALUE": qualifier_source_values,
            }
        )

    def _mock_observation_period_table(self) -> pd.DataFrame:
        """
        Mock the OBSERVATION_PERIOD table with OMOP schema.

        Returns:
            pd.DataFrame: Mocked observation period table data
        """
        # Most patients have 1-3 observation periods (enrollment periods, gaps in coverage, etc.)
        periods_per_patient = np.random.choice(
            [1, 2, 3], size=self.n_patients, p=[0.6, 0.3, 0.1]
        )
        total_periods = periods_per_patient.sum()

        # Generate observation period IDs that look realistic
        observation_period_ids = self._generate_person_ids(
            total_periods, base=10000000
        )  # 8-digit IDs

        # Generate person IDs based on periods per patient
        person_ids = np.repeat(self.base_patient_ids, periods_per_patient)

        # Generate observation periods - these should cover the timeframe of other events
        # Most periods start 2010-2020 and many are still ongoing or end recently
        start_date = datetime(2010, 1, 1)
        end_date = datetime(2020, 1, 1)
        start_date_range = (end_date - start_date).days

        observation_start_dates = []
        observation_end_dates = []

        # Track which patient we're on to create non-overlapping periods for same patient
        current_patient_idx = 0
        current_patient_id = person_ids[0] if total_periods > 0 else None
        last_end_date = None

        for i in range(total_periods):
            # Check if we've moved to a new patient
            if person_ids[i] != current_patient_id:
                current_patient_id = person_ids[i]
                current_patient_idx = 0
                last_end_date = None

            if current_patient_idx == 0:
                # First period for this patient - start randomly between 2010-2020
                period_start = start_date + timedelta(
                    days=int(np.random.uniform(0, start_date_range))
                )
            else:
                # Subsequent period - start after previous period ended (with possible gap)
                if last_end_date:
                    gap_days = np.random.exponential(180)  # Average 6 month gap
                    gap_days = max(30, min(gap_days, 1095))  # 1 month to 3 years gap
                    period_start = last_end_date + timedelta(days=int(gap_days))
                else:
                    # Fallback if something went wrong
                    period_start = start_date + timedelta(
                        days=int(np.random.uniform(0, start_date_range))
                    )

            observation_start_dates.append(period_start.date())

            # Generate end date
            # 70% of periods are ongoing (end in 2024-2025), 30% ended earlier
            if np.random.random() < 0.7:
                # Ongoing - end in 2024-2025
                ongoing_start = datetime(2024, 1, 1)
                ongoing_end = datetime(2025, 12, 31)
                ongoing_range = (ongoing_end - ongoing_start).days
                period_end = ongoing_start + timedelta(
                    days=int(np.random.uniform(0, ongoing_range))
                )
            else:
                # Ended - duration varies (6 months to 10 years)
                duration_days = np.random.exponential(1095)  # Average 3 years
                duration_days = max(
                    180, min(duration_days, 3650)
                )  # 6 months to 10 years
                period_end = period_start + timedelta(days=int(duration_days))

                # Make sure end date isn't in the future
                if period_end > datetime.now():
                    period_end = datetime.now() - timedelta(
                        days=np.random.randint(30, 365)
                    )

            observation_end_dates.append(period_end.date())
            last_end_date = period_end
            current_patient_idx += 1

        # Period type concept IDs (how the observation period was determined)
        period_type_concepts = np.random.choice(
            [
                32817,
                44814722,
                44814723,
                32020,
            ],  # Insurance enrollment, EHR enrollment period, Registry enrollment, EHR
            size=total_periods,
            p=[0.5, 0.25, 0.15, 0.1],
        )

        return pd.DataFrame(
            {
                "OBSERVATION_PERIOD_ID": observation_period_ids,
                "PERSON_ID": person_ids,
                "OBSERVATION_PERIOD_START_DATE": observation_start_dates,
                "OBSERVATION_PERIOD_END_DATE": observation_end_dates,
                "PERIOD_TYPE_CONCEPT_ID": period_type_concepts,
            }
        )

    def _mock_measurement_table(self) -> pd.DataFrame:
        """
        Mock the MEASUREMENT table with OMOP schema.

        Returns:
            pd.DataFrame: Mocked measurement table data
        """
        # Generate measurements for patients - use Poisson distribution for number of measurements per patient
        measurements_per_patient = np.random.poisson(
            lam=8.5, size=self.n_patients
        )  # Average 8-9 measurements per patient
        measurements_per_patient = np.clip(
            measurements_per_patient, 0, 40
        )  # Cap at 40 measurements

        total_measurements = measurements_per_patient.sum()

        # Generate measurement IDs that look realistic
        measurement_ids = self._generate_person_ids(
            total_measurements, base=100000000
        )  # 9-digit IDs

        # Generate person IDs based on measurements per patient
        person_ids = np.repeat(self.base_patient_ids, measurements_per_patient)

        # Common measurement concept IDs (lab tests, vital signs, etc.)
        measurement_concepts = [
            3004410,  # Hemoglobin
            3019550,  # Hematocrit
            3013650,  # White blood cell count
            3024561,  # Serum glucose
            3027114,  # Serum creatinine
            3006906,  # Total cholesterol
            3007220,  # HDL cholesterol
            3028437,  # LDL cholesterol
            3022217,  # Triglycerides
            3019832,  # Hemoglobin A1c
        ]
        measurement_concept_ids = np.random.choice(
            measurement_concepts, size=total_measurements
        )

        # Generate dates - measurement dates over last 5 years (VECTORIZED)
        start_date = datetime(2019, 1, 1)
        end_date = datetime(2024, 12, 31)
        date_range = (end_date - start_date).days

        # Generate all random days at once (vectorized)
        random_days = np.random.uniform(0, date_range, size=total_measurements).astype(
            int
        )
        measurement_dates = [
            start_date + timedelta(days=int(day)) for day in random_days
        ]

        # Generate random hours and minutes during lab hours (vectorized)
        random_hours = np.random.randint(6, 18, size=total_measurements)  # Lab hours
        random_minutes = np.random.randint(0, 60, size=total_measurements)

        # Create datetimes vectorized
        measurement_datetimes = [
            dt + timedelta(hours=int(h), minutes=int(m))  # During lab hours
            for dt, h, m in zip(measurement_dates, random_hours, random_minutes)
        ]

        # Measurement times (string format like "08:30")
        measurement_times = [
            f"{dt.hour:02d}:{dt.minute:02d}" for dt in measurement_datetimes
        ]

        # Measurement type concept IDs (how measurement was performed)
        measurement_type_concepts = np.random.choice(
            [32817, 32020, 44818702, 32810],  # Claim, EHR, Lab result, Physical exam
            size=total_measurements,
            p=[0.3, 0.4, 0.25, 0.05],
        )

        # Generate values, units, and ranges based on measurement type
        value_as_numbers = []
        value_as_concept_ids = []
        unit_concept_ids = []
        unit_source_values = []
        range_lows = []
        range_highs = []
        operator_concept_ids = []
        measurement_source_values = []
        value_source_values = []

        for i, concept_id in enumerate(measurement_concept_ids):
            if concept_id == 3004410:  # Hemoglobin
                hgb = np.random.normal(13.5, 2.0)  # g/dL
                hgb = max(6.0, min(hgb, 20.0))
                value_as_numbers.append(hgb)
                value_as_concept_ids.append(None)
                unit_concept_ids.append(8713)  # g/dL
                unit_source_values.append("g/dL")
                range_lows.append(12.0)
                range_highs.append(16.0)
                measurement_source_values.append("Hemoglobin")
                value_source_values.append(f"{hgb:.1f}")

            elif concept_id == 3019550:  # Hematocrit
                hct = np.random.normal(42, 6)  # %
                hct = max(20, min(hct, 60))
                value_as_numbers.append(hct)
                value_as_concept_ids.append(None)
                unit_concept_ids.append(8554)  # %
                unit_source_values.append("%")
                range_lows.append(36.0)
                range_highs.append(48.0)
                measurement_source_values.append("Hematocrit")
                value_source_values.append(f"{hct:.1f}")

            elif concept_id == 3013650:  # White blood cell count
                wbc = np.random.lognormal(2.0, 0.5)  # 10^3/uL
                wbc = max(1.0, min(wbc, 20.0))
                value_as_numbers.append(wbc)
                value_as_concept_ids.append(None)
                unit_concept_ids.append(8848)  # 10^3/uL
                unit_source_values.append("K/uL")
                range_lows.append(4.5)
                range_highs.append(11.0)
                measurement_source_values.append("WBC")
                value_source_values.append(f"{wbc:.2f}")

            elif concept_id == 3024561:  # Serum glucose
                # Bimodal: fasting (80-100) vs random/diabetic (higher)
                if np.random.random() < 0.6:  # 60% fasting levels
                    glucose = np.random.normal(90, 10)
                    glucose = max(70, min(glucose, 120))
                else:  # 40% random/elevated levels
                    glucose = np.random.lognormal(4.8, 0.4)
                    glucose = max(100, min(glucose, 400))
                value_as_numbers.append(glucose)
                value_as_concept_ids.append(None)
                unit_concept_ids.append(8840)  # mg/dL
                unit_source_values.append("mg/dL")
                range_lows.append(70.0)
                range_highs.append(100.0)
                measurement_source_values.append("Glucose")
                value_source_values.append(f"{glucose:.0f}")

            elif concept_id == 3027114:  # Serum creatinine
                creat = np.random.lognormal(0.0, 0.3)  # mg/dL
                creat = max(0.5, min(creat, 5.0))
                value_as_numbers.append(creat)
                value_as_concept_ids.append(None)
                unit_concept_ids.append(8840)  # mg/dL
                unit_source_values.append("mg/dL")
                range_lows.append(0.7)
                range_highs.append(1.3)
                measurement_source_values.append("Creatinine")
                value_source_values.append(f"{creat:.2f}")

            elif concept_id == 3006906:  # Total cholesterol
                chol = np.random.normal(200, 40)  # mg/dL
                chol = max(100, min(chol, 400))
                value_as_numbers.append(chol)
                value_as_concept_ids.append(None)
                unit_concept_ids.append(8840)  # mg/dL
                unit_source_values.append("mg/dL")
                range_lows.append(None)  # No standard low range
                range_highs.append(200.0)
                measurement_source_values.append("Total Cholesterol")
                value_source_values.append(f"{chol:.0f}")

            elif concept_id == 3007220:  # HDL cholesterol
                hdl = np.random.normal(50, 15)  # mg/dL
                hdl = max(20, min(hdl, 100))
                value_as_numbers.append(hdl)
                value_as_concept_ids.append(None)
                unit_concept_ids.append(8840)  # mg/dL
                unit_source_values.append("mg/dL")
                range_lows.append(40.0)
                range_highs.append(None)  # No standard high range
                measurement_source_values.append("HDL")
                value_source_values.append(f"{hdl:.0f}")

            elif concept_id == 3028437:  # LDL cholesterol
                ldl = np.random.normal(130, 35)  # mg/dL
                ldl = max(50, min(ldl, 300))
                value_as_numbers.append(ldl)
                value_as_concept_ids.append(None)
                unit_concept_ids.append(8840)  # mg/dL
                unit_source_values.append("mg/dL")
                range_lows.append(None)  # No standard low range
                range_highs.append(100.0)
                measurement_source_values.append("LDL")
                value_source_values.append(f"{ldl:.0f}")

            elif concept_id == 3022217:  # Triglycerides
                trig = np.random.lognormal(4.5, 0.5)  # mg/dL
                trig = max(50, min(trig, 500))
                value_as_numbers.append(trig)
                value_as_concept_ids.append(None)
                unit_concept_ids.append(8840)  # mg/dL
                unit_source_values.append("mg/dL")
                range_lows.append(None)  # No standard low range
                range_highs.append(150.0)
                measurement_source_values.append("Triglycerides")
                value_source_values.append(f"{trig:.0f}")

            elif concept_id == 3019832:  # Hemoglobin A1c
                a1c = np.random.lognormal(1.8, 0.3)  # %
                a1c = max(4.0, min(a1c, 15.0))
                value_as_numbers.append(a1c)
                value_as_concept_ids.append(None)
                unit_concept_ids.append(8554)  # %
                unit_source_values.append("%")
                range_lows.append(4.0)
                range_highs.append(5.6)
                measurement_source_values.append("Hemoglobin A1c")
                value_source_values.append(f"{a1c:.1f}")

            else:  # Default case
                value_as_numbers.append(None)
                value_as_concept_ids.append(None)
                unit_concept_ids.append(None)
                unit_source_values.append(None)
                range_lows.append(None)
                range_highs.append(None)
                measurement_source_values.append("Other Measurement")
                value_source_values.append(None)

            # Operator concepts - 10% have operators like >, <, >=
            if np.random.random() < 0.10:
                operator_concept_ids.append(
                    np.random.choice([4172703, 4171754, 4171755])
                )  # >, <, >=
            else:
                operator_concept_ids.append(None)

        # Optional fields with realistic presence rates
        provider_ids = np.where(
            np.random.random(total_measurements) < 0.80,  # 80% have provider
            self._generate_person_ids(total_measurements, base=800000)[
                :total_measurements
            ],
            None,
        )

        visit_occurrence_ids = np.where(
            np.random.random(total_measurements) < 0.75,  # 75% associated with visit
            self._generate_person_ids(total_measurements, base=60000000)[
                :total_measurements
            ],
            None,
        )

        visit_detail_ids = np.where(
            np.random.random(total_measurements) < 0.20,  # 20% have visit detail
            np.random.choice(
                self._get_visit_detail_ids_pool(), size=total_measurements
            ),  # Use consistent IDs
            None,
        )

        measurement_source_concept_ids = np.where(
            np.random.random(total_measurements) < 0.80,  # 80% have source concept
            measurement_concept_ids,  # Same as standard concept for simplicity
            None,
        )

        return pd.DataFrame(
            {
                "MEASUREMENT_ID": measurement_ids,
                "PERSON_ID": person_ids,
                "MEASUREMENT_CONCEPT_ID": measurement_concept_ids,
                "MEASUREMENT_DATE": [dt.date() for dt in measurement_dates],
                "MEASUREMENT_DATETIME": measurement_datetimes,
                "MEASUREMENT_TIME": measurement_times,
                "MEASUREMENT_TYPE_CONCEPT_ID": measurement_type_concepts,
                "OPERATOR_CONCEPT_ID": operator_concept_ids,
                "VALUE_AS_NUMBER": value_as_numbers,
                "VALUE_AS_CONCEPT_ID": value_as_concept_ids,
                "UNIT_CONCEPT_ID": unit_concept_ids,
                "RANGE_LOW": range_lows,
                "RANGE_HIGH": range_highs,
                "PROVIDER_ID": provider_ids,
                "VISIT_OCCURRENCE_ID": visit_occurrence_ids,
                "VISIT_DETAIL_ID": visit_detail_ids,
                "MEASUREMENT_SOURCE_VALUE": measurement_source_values,
                "MEASUREMENT_SOURCE_CONCEPT_ID": measurement_source_concept_ids,
                "UNIT_SOURCE_VALUE": unit_source_values,
                "VALUE_SOURCE_VALUE": value_source_values,
            }
        )

    def get_source_tables(self) -> Dict[str, pd.DataFrame]:
        """
        Get mocked source tables (raw database tables before PhenEx mapping).

        Returns the exact same data on multiple calls for consistency.

        Returns:
            Dict[str, pd.DataFrame]: Dictionary mapping table names to pandas DataFrames containing mock data

        Raises:
            ValueError: If an unknown table is requested that doesn't have a corresponding mock implementation
        """
        # Return cached tables if they exist
        if self._cached_source_tables is not None:
            return self._cached_source_tables

        # Generate tables for the first time
        source_tables = {}
        # Get unique source table names from the domains dictionary
        unique_source_tables = set(
            mapper.NAME_TABLE for mapper in self.domains_dict.domains_dict.values()
        )

        for table_name in unique_source_tables:
            if table_name == "PERSON":
                source_tables[table_name] = ibis.memtable(self._mock_person_table())
            elif table_name == "CONDITION_OCCURRENCE":
                source_tables[table_name] = ibis.memtable(
                    self._mock_condition_occurrence_table()
                )
            elif table_name == "PROCEDURE_OCCURRENCE":
                source_tables[table_name] = ibis.memtable(
                    self._mock_procedure_occurrence_table()
                )
            elif table_name == "DEATH":
                source_tables[table_name] = ibis.memtable(self._mock_death_table())
            elif table_name == "DRUG_EXPOSURE":
                source_tables[table_name] = ibis.memtable(
                    self._mock_drug_exposure_table()
                )
            elif table_name == "VISIT_DETAIL":
                source_tables[table_name] = ibis.memtable(
                    self._mock_visit_detail_table()
                )
            elif table_name == "VISIT_OCCURRENCE":
                source_tables[table_name] = ibis.memtable(
                    self._mock_visit_occurrence_table()
                )
            elif table_name == "OBSERVATION":
                source_tables[table_name] = ibis.memtable(
                    self._mock_observation_table()
                )
            elif table_name == "OBSERVATION_PERIOD":
                source_tables[table_name] = ibis.memtable(
                    self._mock_observation_period_table()
                )
            elif table_name == "MEASUREMENT":
                source_tables[table_name] = ibis.memtable(
                    self._mock_measurement_table()
                )
            else:
                # Raise an error for unknown tables
                supported_tables = [
                    "PERSON",
                    "CONDITION_OCCURRENCE",
                    "PROCEDURE_OCCURRENCE",
                    "DEATH",
                    "DRUG_EXPOSURE",
                    "VISIT_DETAIL",
                    "VISIT_OCCURRENCE",
                    "OBSERVATION",
                    "OBSERVATION_PERIOD",
                    "MEASUREMENT",
                ]
                raise ValueError(
                    f"Unknown table '{table_name}' requested for simulation. "
                    f"Supported tables are: {', '.join(supported_tables)}"
                )

        # Cache the tables for future calls
        self._cached_source_tables = source_tables
        return source_tables

    def get_mapped_tables(self) -> Dict[str, PhenexTable]:
        """
        Get mocked tables mapped to PhenEx representation.

        This mimics the behavior of DomainsDictionary.get_mapped_tables() but with mocked data.

        Returns:
            Dict[str, PhenexTable]: Dictionary mapping domain names to PhenexTable instances containing the mock data ready for use with PhenEx algorithms

        Raises:
            ValueError: If a domain mapper references a table that doesn't have a mock implementation
        """
        source_tables = self.get_source_tables()
        mapped_tables = {}

        for domain, mapper in self.domains_dict.domains_dict.items():
            source_table_name = mapper.NAME_TABLE
            if source_table_name in source_tables:
                mapped_tables[domain] = mapper(source_tables[source_table_name])

        return mapped_tables
