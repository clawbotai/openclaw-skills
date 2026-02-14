import { LightningElement, api } from 'lwc';

export default class PatientDashboard_Standard extends LightningElement {
    @api flowApiName = 'Request_Doctor_Appointment';
}