# PhenEx: Automatic PHENotype EXtractor

<a href="https://github.com/Bayer-Group/PhenEx">
  <div style="text-align: center;">
    <img src="phenex.png" alt="PhenEx Logo" width="500" />
  </div>
</a>

## What is PhenEx?

PhenEx -- pronouned "Phoenix" -- is a cutting-edge framework designed to simplify the extraction and analysis of patient cohorts starting from raw real-world medical data as part of observational study execution. Using a meta-language closely aligned to plain English, PhenEx allows you to define and calculate index dates, inclusion and exclusion criteria, baseline characteristics, and outcome event tables based on arbitrarily complex criteria.

Questions you can answer using PhenEx include, but are not limited to:

- What is the incidence of diabetes among patients aged 50-70?
- How many patients with a history of stroke have also had a diagnosis of atrial fibrillation and prescribed anticoagulants?
- What are the common comorbidities observed in patients with hypertension?
- How do medication adherence rates compare between different patient demographics?
- What proportion of patients who have been diagnosed with breast cancer receive genetic testing for BRCA1 and BRCA2 mutations?
- Among patients treated for acute myocardial infarction (AMI), how many have been re-admitted to the hospital within six months for heart-related issues?
- How many patients with a diagnosis of rheumatoid arthritis have been prescribed at least three different disease-modifying antirheumatic drugs (DMARDs) over their treatment history?

## Who is PhenEx for?

PhenEx is for anyone seeking to analyze real-world patient data, such as claims, electronic health records or disease registries.

- **Pharmaceutical and Biotech Companies**: Accelerate drug development and market access strategies. PhenEx helps you identify patient populations for clinical trials, analyze real-world treatment patterns, and assess the safety and efficacy of new therapies.
- **Epidemiologists and Public Health Professionals**: Conduct comprehensive epidemiological studies and public health surveillance. PhenEx enables you to define and extract complex phenotypes, track health outcomes, and respond to public health challenges effectively.
- **Data Scientists and Analysts**: Simplify the process of data extraction and cohort building. PhenEx provides powerful tools to transform raw data into structured, analysis-ready datasets, enabling you to focus on generating actionable insights.

## Why should I use PhenEx?

1. PhenEx is **free, open-source and interoperable** with a large number of data warehouse backends. Regardless of where you host your data, you can use PhenEx to extract cohorts from it.

2. PhenEx is **data format agnostic**. Whether your data is in the OMOP Common Data Model or something else, PhenEx can handle it with only minimal compatibility transformations. The most common data formats are already built-in and understood by PhenEx.

3. PhenEx supports **complex phenotypes**. PhenEx covers not only basic use cases but also handles arbitrarily complex phenotypes (e.g. ISTH major bleeding, CHADSVASc). With PhenEx, you can define and extract intricate phenotypes, empowering you to tackle a wide range of research questions.

4. PhenEx is **extensible**. If your phenotype is not covered by the existing classes, you can easily create your own implementation using the provided abstract base classes. If you encounter a common pattern that is missing, simply open an issue, and we'll be delighted to consider it for inclusion in the core packages.

5. PhenEx is **scalable**. Whether you have a simple feasibility analysis or a full-blown research protocol with 20 inclusion criteria and 100 baseline characteristics, PhenEx can build your cohort.

6. PhenEx includes a **web application** for non-Python users. Build and visualize cohorts through an intuitive web interface with AI-powered assistance.

7. PhenEx offers **AI integration** to help with cohort building and phenotype definition, making complex studies more accessible.

## What is PhenEx _not_?

- PhenEx does not currently work with unstructured medical data. We make minimal assumptions on the structure of the data, but do require the data to first be in tabular form.

## Getting Started

PhenEx can be used in two ways:

### Python Library

Head on over to the [Official PhenEx Documentation](https://bayer-group.github.io/PhenEx) for comprehensive tutorials and API documentation. If you have any questions, please feel free to reach out to any of the developers and we'll be happy to get you on your way.

### Web Application

PhenEx also includes a user-friendly web application for a visual approach to real-world data analysis. The web app provides:

- Intuitive interface for building cohorts
- AI-powered assistance for phenotype definition
- Visualization of cohort results
- Interactive cohort editing capabilities

To get started with the web app, refer to the deployment instructions in the `app/` directory of the `ui` branch. **The web app is currently in alpha.** Expect bumps in the road as an early user, but also expect priority support as we are eager to get feedback.

## API Stability

Please note that we are adding features at an intense pace. As a result, we cannot always guarantee backwards compatibility when we're making updates. Sometimes new features require new thinking about how things are done.

Therefore, for the 0.\* series of releases we do not guarantee API stability. That means upgrading may break your scripts. We use the convention that 0.X.Y -> 0.X.Z is non-breaking. 0.X.Y -> 0.(X+1).0 may be breaking, but we try to keep breakage to a minimum and "worth it".

If your scripts break upon upgrading, please reach out to one of the developers and we will happily help you. Starting with 1.0, we will not break between minor revisions.
