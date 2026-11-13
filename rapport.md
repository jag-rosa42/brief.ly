# Rapport d’analyse du traitement Ollama

## Conclusion

Le principal problème est la répétition de générations anormalement longues. Le traitement habituel d’un article prend souvent autour d’une seconde ; quelques articles déclenchent des réponses de **4 093 tokens**, puis plusieurs nouvelles tentatives. C’est le premier point à corriger avant de chercher à accélérer la VM ou à paralléliser.

Ce rapport compare les logs fournis au code du dépôt. La durée globale annoncée est d’environ **15 minutes**. Aucun changement du code n’a été effectué pour cette analyse. Le fichier `roadmap.md` était absent du dépôt consulté.

## 1. Bilan de l’exécution

| Indicateur | Résultat |
|---|---:|
| Articles récupérés | 99, en lots de 25 + 25 + 25 + 24 |
| Tentatives de génération pour les articles | 114 |
| Articles acceptés avec résumé | 87 |
| Articles rejetés par une réponse valide du modèle | 9 |
| Articles rejetés automatiquement après épuisement des tentatives | 3 |
| Tentatives échouées | 18 |
| Générations arrêtées avec `done_reason=length` | 9 |
| Erreurs `quality_comment: string_too_long` | 4 |
| Réponses incohérentes : rejet avec résumé | 3 |
| Autres erreurs Ollama | 2 : une erreur dans le flux, un HTTP 500 |
| Appels de synthèse des catégories | 31 |
| Catégories enregistrées | 7 |

Cela représente **145 appels Ollama** : 114 pour les articles et 31 pour les catégories.

Les échanges avec Identity et Content Management affichent tous des réponses HTTP 200. Ollama présente en revanche un cas où **HTTP 200 ne signifie pas une génération réussie** : le serveur commence à répondre, puis signale une erreur dans le flux.

## 2. Pourquoi les 15 minutes sont plausibles

Les neuf générations arrêtées à 4 093 tokens représentent à elles seules :

```text
9 × 4 093 = 36 837 tokens générés sans résultat exploitable
```

Une réponse habituelle dans ces logs produit plutôt quelques dizaines à quelques centaines de tokens. Une seule tentative à 4 093 tokens peut donc consommer autant de génération que plusieurs dizaines d’articles ordinaires.

À titre d’illustration, si ces neuf appels produisaient 50 à 70 tokens par seconde, ils occuperaient environ **9 à 12 minutes**, hors traitement des entrées. Cette estimation explique comment quelques cas peuvent dominer le temps total, mais **ce débit n’est pas mesuré ici**.

Les logs ne permettent pas d’attribuer précisément les 900 secondes :

- Ils n’ont pas d’horodatage.
- Les tentatives échouées n’affichent pas leur durée.
- Les synthèses de catégories n’affichent pas leur durée.
- La préparation et la synchronisation de la VM ne sont pas chronométrées.

La cause dominante est donc fortement suspectée, sans ventilation temporelle complète.

## 3. Priorité maximale : limiter explicitement les tokens de sortie

Dans `srcs/services/ai-processing/src/infrastructure/clients/OllamaSummarizerClient.py`, les options définissent `temperature` et `num_ctx`, mais pas `num_predict`.

Ces paramètres ont des rôles différents :

| Paramètre | Rôle |
|---|---|
| `num_ctx` | Capacité de contexte utilisée pour le traitement |
| `num_predict` | Nombre maximal de tokens générés |

Ollama permet de fixer ce budget de sortie avec `num_predict`. Voir la [documentation officielle](https://docs.ollama.com/modelfile#valid-parameters-and-values).

**Amélioration proposée :** essayer un budget de départ de **256 à 384 tokens pour les évaluations d’articles**, puis le calibrer sur un échantillon représentatif. Prévoir un budget distinct pour les catégories.

Le budget doit permettre de terminer le JSON. Une sortie coupée reste invalide : il ne faut pas enregistrer un résumé incomplet pour gagner du temps.

**Vérification :** mesurer la durée totale, le taux de réponses valides et la qualité des résumés sur les mêmes articles, notamment les six articles ayant nécessité plusieurs tentatives.

## 4. Priorité maximale : adapter les nouvelles tentatives à l’erreur

Le comportement actuel est confirmé dans `srcs/services/ai-processing/src/application/SummarizeArticles.py` :

- Une erreur de validation fournit un retour correctif au modèle.
- Une erreur `length` produit un `ValueError`, puis relance la demande sans retour correctif.
- Chaque article peut subir quatre tentatives.

Avec une température à zéro, une demande identique a davantage de chances de reproduire le même échec. C’est exactement le motif observé pour `ba2f6075…` et `a225ae19…`.

| Erreur | Traitement proposé |
|---|---|
| Sortie trop longue | Nouvelle tentative courte avec consigne adaptée et budget borné |
| Commentaire trop long | Correction ciblée sur ce champ |
| Rejet avec résumé | Correction explicite de la relation entre les champs |
| Erreur serveur temporaire | Nouvelle tentative limitée, avec délai progressif |
| Même erreur répétée | Arrêt anticipé et statut d’échec technique |

Ajouter également un **budget de temps cumulé par article**, plutôt qu’un simple nombre de tentatives.

Pour `d0c63a7a…`, les trois dernières réponses produisent exactement 146 tokens et échouent sur la même règle. C’est un indice fort que les tentatives supplémentaires n’apportent plus rien.

**Vérification :** reproduire chaque famille d’erreur et vérifier le nombre d’appels, le retour correctif envoyé, le temps cumulé et l’état final enregistré.

## 5. Priorité élevée : distinguer rejet éditorial et échec technique

Après quatre échecs, le code enregistre `rejected=True`.

Cela mélange deux situations :

- Le modèle a évalué le contenu et l’a jugé inutilisable.
- Le système n’a pas obtenu de réponse valide.

**Les trois rejets automatiques ne prouvent donc pas que les articles sont mauvais.**

Il faudrait distinguer, dans le stockage ou au minimum dans le suivi, un état `generation_failed` d’un rejet de contenu. Cela permettrait de retraiter ces articles après correction et de calculer un taux de rejet éditorial fiable.

Les trois articles finalement rejetés par le modèle à leur troisième tentative méritent aussi une vérification manuelle : leurs réponses sont valides techniquement, mais les logs seuls ne permettent pas de juger leur décision.

**Vérification :** un échec technique doit rester identifiable et retraitable ; un rejet éditorial doit correspondre à une décision valide du modèle.

## 6. Priorité élevée : améliorer le contrat de sortie

Le code retire volontairement `minLength` et `maxLength` du schéma envoyé à Ollama, à cause de problèmes de complexité de grammaire. Les limites restent dans le prompt et dans la validation locale.

Conséquence : **le JSON peut respecter la structure attendue tout en étant trop long**. Les quatre erreurs sur `quality_comment` illustrent cette limite.

Améliorations possibles :

- Demander un commentaire réellement bref, avec un exemple de rejet.
- Rendre plus explicite la règle `rejected=true → summary=null`.
- Tester un schéma distinguant les branches « accepté » et « rejeté », si la version d’Ollama le supporte correctement.
- Examiner les réponses défaillantes dans un cadre de diagnostic contrôlé, sans déverser les contenus dans les logs courants.

Il faut conserver la validation métier : elle empêche ici l’enregistrement de réponses incohérentes.

**Vérification :** comparer les taux d’erreurs de longueur et de cohérence sur un corpus fixe, en conservant les limites du contrat métier.

## 7. Priorité élevée : mesurer aussi les échecs

Aujourd’hui, les logs mettent surtout en évidence les appels rapides réussis. Les appels potentiellement les plus coûteux terminent par une trace d’erreur sans `elapsed`.

À ajouter :

- Horodatage des logs.
- Durée de chaque tentative, réussie ou échouée.
- Durée cumulée par article.
- Durée des phases préparation, articles et catégories.
- Bilan final : volumes, erreurs et temps consommé.

Ollama fournit notamment `total_duration`, `load_duration`, `prompt_eval_duration` et `eval_duration`, utiles pour séparer chargement, lecture de l’entrée et génération. Voir la [documentation officielle](https://github.com/ollama/ollama/blob/main/docs/api.md).

Pour Prometheus, utiliser des labels bornés tels que `phase`, `outcome` et `error_kind`. **Aucun UUID d’article, titre ou contenu dans les labels**, et conserver Prometheus, Pushgateway et `/metrics` internes.

**Vérification :** le bilan doit permettre d’expliquer le temps total, y compris les tentatives échouées, sans introduire de labels à forte cardinalité.

## 8. Priorité secondaire : réduire le coût des catégories

Les 31 appels de catégories s’expliquent par la réduction hiérarchique actuelle : le code combine les résumés par groupes de quatre, puis combine les résultats. Ce ne sont pas des retries visibles.

| Catégorie | Appels |
|---|---:|
| Business | 4 |
| Entertainment | 5 |
| General | 3 |
| Health | 3 |
| Science | 5 |
| Sports | 7 |
| Technology | 4 |

Augmenter la taille des groupes pourrait diminuer le nombre d’appels, mais peut aussi dégrader la couverture des faits. Il faut comparer temps et qualité.

Autre amélioration : **ne recalculer une catégorie que si ses entrées ont changé**. Sur cette exécution, aucun échec de catégorie n’apparaît.

**Vérification :** mesurer le nombre d’appels et la durée, puis vérifier que les faits importants restent représentés et qu’aucun fait absent des entrées n’est ajouté.

## 9. Corriger un défaut dans les métriques

Dans `srcs/services/ai-processing/src/application/SummarizeArticles.py`, à la ligne 119 au moment de l’inspection, la boucle de rejet final réutilise `assessment` et `started_at` d’une tentative précédente pour éventuellement compter un succès.

Ce bloc peut produire une métrique incorrecte ; si aucune évaluation n’a réussi, `assessment` peut même ne pas être défini.

Il faut supprimer ce comptage de succès dans le traitement des échecs finaux. Ce défaut n’explique pas les 15 minutes, mais compromet la fiabilité du diagnostic.

**Vérification :** un lot dont toutes les générations échouent doit terminer sans erreur de variable et sans incrémenter le compteur de résumés réussis.

## 10. Ordre de travail recommandé

1. Mesurer les durées manquantes pour disposer d’une référence.
2. Borner les tokens et le temps cumulé par article.
3. Adapter les retries et arrêter les échecs répétitifs.
4. Séparer échec technique et rejet éditorial.
5. Corriger les métriques.
6. Optimiser les catégories.
7. Évaluer ensuite une concurrence limitée ou un autre modèle.

**La parallélisation ne serait pas le premier changement recommandé.** Le traitement est séquentiel, mais lancer simultanément plusieurs générations de 4 093 tokens pourrait accroître la contention. Le gain le plus prometteur consiste d’abord à empêcher quelques réponses inutilisables de monopoliser l’exécution.

Les modifications proposées doivent être évaluées sur un corpus fixe, avec comparaison du temps total, du taux de réponses valides et de la qualité des résultats. Aucun objectif de durée précise ne peut être garanti avec les seules mesures disponibles dans ces logs.
