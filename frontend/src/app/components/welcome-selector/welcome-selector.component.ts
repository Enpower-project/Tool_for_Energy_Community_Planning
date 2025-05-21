import { Component, EventEmitter, Input, OnInit, Output, OnChanges } from '@angular/core';
import { FormGroup, FormBuilder, Validators } from '@angular/forms';
import { CardInfo, cardBussinessArray } from '../../data/types';
import { KeycloakService } from 'keycloak-angular';
import { KeycloakToolsService } from '../../services/keycloak-tools.service';
import { FindCommunityService } from '../../services/find-community.service';

/**
 * Welcome page 
 *
 * @export
 * @class WelcomeSelectorComponent
 * @typedef {WelcomeSelectorComponent}
 * @implements {OnInit}
 */
@Component({
  selector: 'app-welcome-selector',
  templateUrl: './welcome-selector.component.html',
  styleUrls: ['./welcome-selector.component.scss']
})
export class WelcomeSelectorComponent implements OnInit, OnChanges {

  @Input() triggerReload: boolean = false;

  /**
   * Index of selected card 
   *
   * @type {number}
   */
  @Input() selectedCard: number = -1;
  /**
   * Enable show all cards
   *
   * @type {boolean}
   */
  /**
   * Limit of card you can see 
   *
   * @type {number}
   */
  @Input() limit: number = 4;
  /**
   * Anable show ONBOARDING modal
   *
   * @type {boolean}
   */
  @Input() isOpenModal: boolean = false;
  /**
   * Allows you go back in the app navigation
   *
   * @type {*}
   */
  @Output() goBack = new EventEmitter();
  /**
   * Allows you close the formulary and return to home
   *
   * @type {*}
   */
  @Output() close = new EventEmitter();
  /**
   * Allows you go to the next page
   *
   * @type {*}
   */
  @Output() next = new EventEmitter();

  @Output() createNewCommunity = new EventEmitter();

  /**
   * Formgroup
   *
   * @type {FormGroup}
   */
  form: FormGroup = new FormGroup({});
  /**
   * Cards information array
   *
   * @type {CardInfo[]}
   */
  bussinessCards: CardInfo[] = cardBussinessArray


  public disableAlternativeButton: boolean = false;

  public message: string = "";

  public communityList: any;

  private openCreateCommunity: boolean = false;

  public openModalCreateCommunity: boolean = false;

  /**
   * Creates an instance of WelcomeSelectorComponent.
   *
   * @constructor
   * @param {FormBuilder} formBuilder
   */
  constructor(
    private formBuilder: FormBuilder,
    private readonly keycloak: KeycloakService,
    private keyToolsService: KeycloakToolsService,
    private findCommunityService: FindCommunityService
  ) { }

  /**
   * OnInit
   */
  ngOnInit() {
    this.reloadAlternativeOption();
    this.setForm();
  }

  ngOnChanges() {
    if (this.triggerReload) {
      this.reloadAlternativeOption();
    }
  }

  private reloadAlternativeOption() {
    this.disableAlternativeButton = true;
    if (!this.keycloak.isLoggedIn()) {
      this.message = "ONBOARDING.ALERT.NO_LOG_IN";
      this.disableAlternativeButton = true;
    } else {
      this.disableAlternativeButton = false;
      this.message = "";
      this.keyToolsService.getUserUID().then(uid => {
        this.findCommunityService.getCommunityList().subscribe({
          next: (data: any) => {
            this.communityList = data.filter((da: any) => da.author === uid);
            this.openCreateCommunity = this.communityList?.length === 0;
          }, error: (err: any) => {
            console.error(err.message)
          }
        })

      });
    }
  }

  /**
   * Set from configuration
   *
   * @public
   */
  public setForm() {
    this.form = this.formBuilder.group({
      option: [this.selectedCard, Validators.required],
    });

  }

  /**
   *  Allows you go back in the app navigation
   *
   * @public
   */
  public back() {
    this.goBack.emit();
  }

  /**
   * Allows you close the formulary and return to home
   *
   * @public
   */
  public closeIt() {
    this.close.emit();
  }

  /**
   * Allows you go to the next page
   *
   * @public
   */
  public goNext() {
    this.next.emit(this.selectedCard);
  }

  /**
   * Allows you to show more or less cards
   */

  /**
   * Allows you select a card
   *
   * @public
   * @param {*} cardItem
   * @param {number} position
   */
  public selectCard(cardItem: any, position: number) {

    if (!cardItem.validate){
      this.selectedCard = position;
      this.goNext();
    }
    else if (this.disableAlternativeButton === false && !this.openCreateCommunity){
      this.selectedCard = position;
      this.goNext();
    }
    else if (this.openCreateCommunity) {
      this.openModalCreateCommunity = true;
    }

  }

  /**
   * Close the modal
   *
   * @public
   */
  public closeModal() {
    this.isOpenModal = false;
  }

  /**
   * Open the modal
   *
   * @public
   */
  public openModal() {
    this.isOpenModal = true;
  }

  public goToCreateCommunity() {
    this.openModalCreateCommunity = false;
    this.createNewCommunity.emit();
  }

}