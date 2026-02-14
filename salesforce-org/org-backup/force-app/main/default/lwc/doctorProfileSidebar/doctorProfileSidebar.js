import { LightningElement, wire } from 'lwc';
import getDoctorProfile from '@salesforce/apex/AzothDoctorController.getDoctorProfile';

export default class DoctorProfileSidebar extends LightningElement {
    doctor;
    initials = 'DR';

    @wire(getDoctorProfile)
    wiredProfile({ error, data }) {
        if (data) {
            this.doctor = data;
            this.setInitials(data.Name);
        } else if (error) {
            console.error('Error loading profile', error);
        }
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