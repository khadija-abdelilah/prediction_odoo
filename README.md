# newcomers

Projet d'intégration sur Odoo 13.0 CE

## Description du module

**Gestion des interventions**

  Une intervention est une mobilisation d’une ou plusieurs ressources humaines et matériels (Compagnons, fournitures, déplacements) pour répondre à une demande formulée par un client ou un conducteur de travaux pour intervenir sur une urgence ou une demande de SAV.

   Une intervention est planifiée sur un seul créneau ou plusieurs créneaux. Dans ce dernier cas, on parle de suite d’interventions. Une intervention concerne un corps d’état particulier (Electricité, Plomberie, …ou tout corps d’état).

   Les interventions peuvent aussi donner lieu à des facturations clients. Les interventions sont facturées soit séparément ou regroupées dans une seule facture pour le même client. Les factures sont destinées soit directement au client concerné par l’intervention ou un tiers payeurs. (Syndic, Foncier, …).


**Les différentes natures d’intervention :**

*  Intervention de prise de rendez-vous : Correspond à la prise de rendez-vous du chargé d’affaires chez le client pour établir un devis. Le déplacement du chargé d’affaire est parfois facturé au client. Cette intervention peut être effectuée dans le cadre d’une affaire « Régie », « Chantier » ou « Maintenance »

*  Intervention de chantier : Des interventions qui peuvent être dans le cadre d’un chantier sans facturation supplémentaire. (SAV, GPA, RG, Demande de devis…)

*  Suite d’intervention : Pour faire suite à une intervention déjà passée mais dont la prestation n’est pas encore finalisée.

*  Interventions de maintenance : Interventions planifiées à la signature d’un contrat de maintenance sur une longue durée.

*  Intervention de dépannage : Intervention qui rentre dans le cadre des affaires de régie.


**Remarque** : Une intervention peut concerner plusieurs corps d’état, dans ce cas, seul le corps d’état dominant prime.

**Processus métier**

![processus](/uploads/5be0de53e45297d29bf820d1f8b2e578/processus.png)



**Création de l’intervention**

Une intervention est créée par l’assistante suite à :

*  Une demande d’un client par O.S., Email, Fax ou Tél.
*  Ou à la création d’un contrat de maintenance.

L’assistante renseigne les informations de l’intervention :

*  Le corps de métier de l’intervention
*  Affaire associée à l’intervention
*  La nature de l’intervention
*  Le type de paiement : Sur place, pour récupérer le paiement du client par le compagnon à l’issue de son
   intervention ou au bureau dans le cas où le client peut émettre le chèque au bureau.
*  Le tiers payeur si celui-ci est différent du client.
*  Le détail du rendez-vous (adresse du chantier, intervenants, …)

  L’assistante propose au client la date (ou les dates d’intervention). La planification de l’intervention des ressources est effectuée, à cet effet, à la confirmation des dates par le client.

**Exécution de l’intervention**

   A l’issue de l’intervention, l’intervenant communique à l’assistante du pôle porteur de l’affaire, le compte rendu de l’intervention et la liste des fournitures utilisées au magasinier depuis son véhicule.
   Le CR est transmis par mail au client dans la foulée. Le magasinier, réassorti le véhicule par les mêmes fournitures et impute ses fournitures sur l’affaire et l’intervention associée.

   L’assistante récupère le compte rendu puis saisit ainsi le temps passé en minutes et contrôle les fournitures consommées remontées par le magasinier.

**Remarque :**

Dans certains cas, l’intervenant a besoin d’acheter des fournitures pour accomplir sa tâche. Il contacte,à cet effet, l’assistante qui émet un bon de commande d’achat. Ce dernier est rattaché à l’intervention et remonte dans la facturation.

**Clôture de l’intervention**

Avant de clore l’intervention, l’assistante génère la facture associée à une ou plusieurs interventions,
met à jour le prix des prestations à facturer, arrondit les temps des interventions au chiffre supérieur,
met à jour l’adresse de facturation si nécessaire, le tiers payeur et adapte le coefficient de facturation.
Le temps des prestations est exprimé en heures sur la facture. Le CR de l’intervention (des
interventions) est aussi généré pour le transmettre chez le client avec la facture (ou les factures) associée(s). Les factures reprennent le détail de la main d’œuvre et des achats effectués. Les factures peuvent aussi être globales.
