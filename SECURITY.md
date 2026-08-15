# Politique de sécurité

## Signaler une vulnérabilité

Merci de ne pas ouvrir d'issue publique pour une faille de sécurité.
Contactez plutôt directement le mainteneur à
[hervecedricyouan@gmail.com](mailto:hervecedricyouan@gmail.com) avec :

- une description du problème et de son impact ;
- les étapes de reproduction ;
- la version de `django-forge-log` concernée.

Une réponse est visée sous 5 jours ouvrés.

## Points d'attention spécifiques à un audit trail

`django-forge-log` journalise potentiellement des données sensibles (valeurs
avant/après des champs modifiés). Avant de signaler une fuite de PII comme
un bug applicatif, vérifiez d'abord `FORGE_LOG["EXCLUDED_FIELDS"]` et
`FORGE_LOG["MASKED_FIELDS"]` — voir le README, section Sécurité et PII. Un
défaut de configuration côté projet utilisateur n'est pas une vulnérabilité
de la librairie, mais toute lacune dans les valeurs par défaut fournies
(champs sensibles courants non couverts) en est une et doit être signalée.
