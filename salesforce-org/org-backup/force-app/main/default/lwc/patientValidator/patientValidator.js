import { LightningElement, api, wire, track } from 'lwc';
import { CurrentPageReference } from 'lightning/navigation';
import validatePatient from '@salesforce/apex/PatientValidationController.validatePatient';
import getPatientName from '@salesforce/apex/PatientValidationController.getPatientName';
import getValidationStatus from '@salesforce/apex/PatientValidationController.getValidationStatus';

export default class PatientValidator extends LightningElement {
    @api recordId;
    @track patientName;
    @track isValidated = false;
    @track isLoading = true;
    @track error;

    @wire(CurrentPageReference)
    getStateParameters(currentPageReference) {
        if (currentPageReference) {
            this.recordId = currentPageReference.state.recordId;
            this.loadPatientData();
        }
    }

    connectedCallback() {
        if (this.recordId) {
            this.loadPatientData();
        }
    }

    loadPatientData() {
        this.isLoading = true;
        this.error = null;

        getPatientName({ accountId: this.recordId })
            .then(result => {
                this.patientName = result;
                return getValidationStatus({ accountId: this.recordId });
            })
            .then(status => {
                if (status === 'Validated') {
                    this.isValidated = true;
                }
                this.isLoading = false;
            })
            .catch(error => {
                this.error = 'Error loading patient data: ' + (error.body ? error.body.message : error.message);
                this.isLoading = false;
            });
    }

    handleValidate() {
        this.isLoading = true;
        this.error = null;

        validatePatient({ accountId: this.recordId })
            .then(() => {
                this.isValidated = true;
                this.isLoading = false;
            })
            .catch(error => {
                this.error = 'Error validating patient: ' + (error.body ? error.body.message : error.message);
                this.isLoading = false;
            });
    }
}