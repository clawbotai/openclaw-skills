import { LightningElement, wire } from 'lwc';
import getPatientProfile from '@salesforce/apex/AzothPatientController.getPatientProfile';

export default class PatientProfileSidebar extends LightningElement {
    patient;
    initials = 'PT';

    @wire(getPatientProfile)
    wiredProfile({ error, data }) {
        if (data) {
            this.patient = data;
            this.setInitials(data.Name);
        } else if (error) {
            console.error('Error loading profile', error);
        }
    }

    get doctorName() {
        return this.patient?.Account?.Doctor__r?.Name || '';
    }

    get doctorLicense() {
        return this.patient?.Account?.Doctor__r?.Medical_License__c || '';
    }

    setInitials(name) {
        if (!name) return;
        const parts = name.split(' ');
        if (parts.length >= 2) {
            this.initials = (parts[0][0] + parts[1][0]).toUpperCase();
        } else {
            this.initials = name.substring(0, 2).toUpperCase();
        }
    }
}