# Rules

**Semantic naming**: nommer composants, props et variants selon leur rôle et leur intention réelle. 
(ex: Header ❌ → Navbar ✅)

**HTML semantics**: conserver les conventions HTML lorsque créer une abstraction supplémentaire n'apporte pas de valeur. 
(ex: subheading ❌ → h3 ✅)

**Framework conventions**: utiliser les primitives et conventions natives de React, TypeScript et React Router. 
(ex: path="/" ❌ → index ✅)

**Strong typing**: représenter les ensembles finis avec des unions/types précis plutôt qu'avec des string génériques. 
(ex: variant: string ❌ → variant: ButtonVariant ✅)

**Reuse existing types**: étendre les types React/DOM existants plutôt que de recréer leurs APIs. 
(ex: props custom complètes ❌ → ButtonHTMLAttributes<HTMLButtonElement> ✅)

**Single responsibility**: séparer les composants ayant des responsabilités ou des sémantiques différentes. 
(ex: ButtonLink ❌ → Button + Link ✅)

**DRY & composition**: extraire les composants, styles et layouts communs au lieu de dupliquer le code. 
(ex: <Layout> répété ❌ → route parent <Layout /> ✅)

**Keep code simple**: supprimer les abstractions, branches, props et déclarations qui n'apportent aucune valeur. 
(ex: switch(getTextTag()) ❌ → const Component = getTextTag() ✅)
