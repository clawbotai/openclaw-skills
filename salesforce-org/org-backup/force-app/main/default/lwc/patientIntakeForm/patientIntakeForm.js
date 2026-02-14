import { LightningElement, track, wire } from 'lwc';
import { createRecord } from 'lightning/uiRecordApi';
import submitIntake from '@salesforce/apex/AzothIntakeController.submitIntake';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

export default class PatientIntakeForm extends LightningElement {
    @track isSuccess = false;
    @track createdAccountId;
    @track debugError; // Stores raw error for debugging

    // Identity Data
    @track firstName = '';
    @track lastName = '';
    @track email = '';
    @track phone = '';
    @track idType = 'Cédula de Ciudadanía';
    @track idNumber = '';
    @track coldChainAuth = false;

    // Legal Data
    @track habeasData = false;
    @track magistralConsent = false;

    // Wellness Data
    @track weight = '';
    @track height = '';
    @track waist = '';
    @track isPregnancy = false;
    @track isCancer = false;
    @track isPancreatitis = false;
    @track isInsulin = false;

    get isFormVisible() {
        return !this.isSuccess;
    }

    connectedCallback() {
        try {
            const search = window.location.search;
            if (search) {
                const urlParams = new URLSearchParams(search);
                this.slug = urlParams.get('ref') || '';
            }
        } catch (e) {
            console.error('URL Parsing error', e);
        }
    }

    get welcomeMessage() {
        return `Patient Intake`;
    }

    handleInputChange(event) {
        const field = event.target.dataset.field;
        const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
        this[field] = value;
    }

    validateAll() {
        return this.firstName &&
            this.lastName &&
            this.email &&
            this.idNumber &&
            this.weight &&
            this.height &&
            this.habeasData &&
            this.magistralConsent;
    }

    handleSubmit() {
        if (!this.validateAll()) {
            this.showToast('Required Fields', 'Please complete all required fields (Identity, Clinical, and Legal Consents).', 'warning');
            return;
        }

        this.isLoading = true;
        const isHighRisk = this.isPregnancy || this.isCancer || this.isPancreatitis || this.isInsulin;

        let safetyAlerts = '';
        if (this.isPregnancy) safetyAlerts += 'Pregnancy/Breastfeeding; ';
        if (this.isCancer) safetyAlerts += 'Active Malignancy; ';
        if (this.isPancreatitis) safetyAlerts += 'Pancreatitis; ';
        if (this.isInsulin) safetyAlerts += 'Insulin Use; ';

        const intakeData = {
            firstName: this.firstName,
            lastName: this.lastName,
            email: this.email,
            phone: this.phone,
            idType: this.idType,
            idNumber: this.idNumber,
            weight: this.weight,
            height: this.height,
            isPregnancy: this.isPregnancy,
            isCancer: this.isCancer,
            isInsulin: this.isInsulin,
            isHighRisk: isHighRisk,
            coldChainAuth: this.coldChainAuth
        };

        submitIntake({ intakeData: intakeData, doctorSlug: this.slug })
            .then((resultId) => {
                this.createdAccountId = resultId;
                this.isSuccess = true;
                window.scrollTo(0, 0);
                this.showToast('Success', 'Assessment Received (v2 - Apex)', 'success');
            })
            .catch(error => {
                const message = error.body ? error.body.message : 'Unknown Error';
                this.showToast('Submission Error', message, 'error');
            })
            .finally(() => {
                this.isLoading = false;
            });
    }

    showToast(title, message, variant) {
        this.dispatchEvent(new ShowToastEvent({ title, message, variant }));
    }
}