import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { APP_ROUTES } from '../../../data/routes';
import { KeycloakService } from 'keycloak-angular';

@Component({
  selector: 'app-alternatives',
  templateUrl: './alternatives.component.html',
  styleUrls: ['./alternatives.component.scss']
})
export class AlternativesComponent implements OnInit {

  private communityID?: number;

  constructor(private router: Router,
    private readonly keycloak: KeycloakService,
    private activatedRoute: ActivatedRoute

  ) { }

  ngOnInit() {
    const isLoggedIn = this.keycloak.isLoggedIn();
    if (!isLoggedIn) {
     this.keycloak.login();
    }else{
      this.activatedRoute.params.subscribe(params => {
        const paramId = params['id'];
        this.communityID = Number(paramId);
      });
    }
  }

  public generateNewCommunity(){
    this.router.navigate(["/" + APP_ROUTES.FORMULARY, this.communityID], { queryParams: { create_alternatives: 'true' } });
  }

}
