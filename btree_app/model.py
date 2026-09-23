
from __future__ import annotations

import copy


class Node:
    def __init__(self, leaf=True):
        self.leaf = leaf
        self.keys = []
        self.children = []


class BTree:
    def __init__(self, t=2):
        if t < 2:
            raise ValueError("El grado mínimo t debe ser >= 2.")
        self.t = t
        self.root = Node(True)
        self.narration = []
        self._touched = set()
        self.history = []  


    def _log(self, texto):
        self.narration.append(texto)

    def _record(self, titulo, before=None, process=None):
        snap = copy.deepcopy(self.root)
        texto = "\n".join(f"{i+1}. {s}" for i, s in enumerate(self.narration))
  
        texto += "\n\nInvariantes mantenidas:"
        texto += f"\n  • Todos los caminos de la raíz a una hoja tienen la misma longitud."
        texto += f"\n  • Cada nodo (excepto la raíz) tiene entre t-1={self.t-1} y 2t-1={2*self.t-1} claves."
        texto += f"\n  • La raíz tiene entre 1 y 2t-1={2*self.t-1} claves (si no está vacía)."
        if process is None:
            joined = "\n".join(self.narration)
            if "se realiza un SPLIT" in joined or "→ SPLIT" in joined:
                process = "split"
            elif "Se fusionan (COALESCE)" in joined:
                process = "merge"
            elif "Se toma PRESTADO" in joined:
                process = "borrow"
            else:
                process = None
        self.history.append({
            "title": titulo,
            "text": texto,
            "tree": snap,
            "before": before,
            "process": process,
            "t": self.t,
            "touched": set(self._touched),
        })


    def search(self, k):
        self.narration = []
        self._touched = set()
        before = copy.deepcopy(self.root)
        self._log(
            f"Se desea buscar la clave {k}. "
            f"Se parte de la raíz. En cada nodo interno se compara k con las claves del nodo "
            f"para elegir el hijo correcto (hay un puntero/hijo entre cada par de claves, "
            f"más uno a la izquierda del mínimo y uno a la derecha del máximo)."
        )
        found = self._search(self.root, k)
        if found:
            self._touched.add(k)
            self._log(
                f"La clave {k} SÍ está en el árbol. "
                f"La búsqueda en un Árbol B recorre un único camino de la raíz a una hoja "
                f"(o al nodo interno donde está la clave), comparando en cada nodo interno "
                f"para decidir por cuál de los (hasta 2t) hijos descender. "
                f"Grado t={self.t} ⇒ factor de ramificación entre t y 2t hijos por nodo interno."
            )
        else:
            self._log(
                f"La clave {k} NO se encontró. Se exploró un camino completo hasta un nodo hoja "
                f"sin hallarla. En un Árbol B todas las hojas están al mismo nivel "
                f"(propiedad de balanceo), así que el coste es O(log_t n)."
            )
        self._record(f"Búsqueda de {k}", before=before)
        return found

    def _search(self, x, k):
        i = 0
        while i < len(x.keys) and k > x.keys[i]:
            i += 1
        if i < len(x.keys) and x.keys[i] == k:
            self._log(
                f"En el nodo con claves {x.keys} se encontró la clave {k} "
                f"en la posición {i}."
            )
            return True
        if x.leaf:
            self._log(
                f"Se llegó a un nodo HOJA {x.keys} (las hojas no tienen hijos) sin encontrar {k}."
            )
            return False
        if i == 0:
            cmp = f"es menor que la primera clave ({x.keys[0]})"
        elif i == len(x.keys):
            cmp = f"es mayor que la última clave ({x.keys[-1]})"
        else:
            cmp = f"está entre {x.keys[i-1]} y {x.keys[i]}"
        self._log(
            f"En el nodo interno {x.keys}, la clave {k} {cmp}; "
            f"se desciende por el hijo en la posición {i}."
        )
        return self._search(x.children[i], k)

  

    def insert(self, k):
        self.narration = []
        self._touched = {k}
        t = self.t
        before = copy.deepcopy(self.root)
        self._log(
            f"Se desea insertar la clave {k}. "
            f"(Árbol B de grado t={self.t}: cada nodo no-raíz tiene entre t-1={self.t-1} "
            f"y 2t-1={2*self.t-1} claves; la raíz entre 1 y 2t-1; todas las hojas al mismo nivel.)"
        )
        if self._contains(self.root, k):
            self._log(
                f"La clave {k} ya existe en el árbol. Este simulador no admite "
                f"claves duplicadas (cada clave debe ser única), así que la "
                f"inserción se cancela y el árbol queda sin cambios."
            )
            self._touched = set()
            self._record(f"Intento fallido de insertar {k} (duplicada)", before=before)
            return
        r = self.root
        if len(r.keys) == 2 * t - 1:
            self._log(
                f"La raíz tiene {len(r.keys)} claves, el máximo permitido "
                f"(2t-1 = {2*t-1}); está llena. Se crea una nueva raíz vacía, "
                f"la raíz anterior pasa a ser su único hijo y se divide de forma "
                f"preventiva ANTES de bajar más. Esta es la única forma en que un "
                f"Árbol B crece en altura."
            )
            s = Node(False)
            s.children.append(r)
            self.root = s
            self._split_child(s, 0)
            r = s
        self._insert_nonfull(r, k)
        self._record(f"Inserción de {k}", before=before)

    def _split_child(self, x, i):
        t = self.t
        y = x.children[i]
        z = Node(y.leaf)
        mid = y.keys[t - 1]
        izq = y.keys[: t - 1]
        der = y.keys[t:]
        self._touched.add(mid)
        self._log(
            f"El nodo con claves {y.keys} superó la capacidad máxima de "
            f"2t-1 = {2*t-1} claves → SPLIT (división). "
            f"La clave mediana {mid} asciende al padre (que tenía {list(x.keys)}). "
            f"Quedan dos nodos: izquierdo {izq} ({len(izq)} claves) y derecho {der} ({len(der)} claves). "
            f"El padre gana un hijo más (factor de ramificación +1 en ese nodo)."
        )
        z.keys = der
        if not y.leaf:
            z.children = y.children[t:]
            y.children = y.children[:t]
        y.keys = izq
        x.children.insert(i + 1, z)
        x.keys.insert(i, mid)

    def _insert_nonfull(self, x, k):
        t = self.t
        i = len(x.keys) - 1
        if x.leaf:
            while i >= 0 and k < x.keys[i]:
                i -= 1
            x.keys.insert(i + 1, k)
            self._log(
                f"Se llegó a un nodo hoja que no está lleno ({len(x.keys)-1} "
                f"claves antes de insertar). Se inserta {k} en su posición "
                f"ordenada. Claves del nodo tras la inserción: {x.keys}."
            )
        else:
            while i >= 0 and k < x.keys[i]:
                i -= 1
            i += 1
            if i == 0:
                cmp = f"es menor que la primera clave del nodo ({x.keys[0]})"
            elif i == len(x.keys):
                cmp = f"es mayor que la última clave del nodo ({x.keys[-1]})"
            else:
                cmp = f"está entre {x.keys[i-1]} y {x.keys[i]}"
            self._log(
                f"En el nodo interno con claves {x.keys}, la clave {k} {cmp}; "
                f"por lo tanto se desciende por el hijo en la posición {i}."
            )
            if len(x.children[i].keys) == 2 * t - 1:
                self._split_child(x, i)
                if k > x.keys[i]:
                    i += 1
            self._insert_nonfull(x.children[i], k)

  

    def delete(self, k):
        self.narration = []
        self._touched = {k}
        before = copy.deepcopy(self.root)
        self._log(
            f"Se desea eliminar la clave {k}. "
            f"La eliminación en Árbol B debe preservar el balanceo: si un nodo queda con "
            f"menos de t-1={self.t-1} claves se reequilibra con PRESTAMO (borrow) de un "
            f"hermano o FUSION (merge/coalesce) con un hermano y la clave separadora del padre."
        )
        if not self._contains(self.root, k):
            self._log("La clave no existe en el árbol; no se realiza ningún cambio.")
            self._touched = set()
            self._record(f"Intento fallido de eliminar {k}", before=before)
            return
        self._delete(self.root, k)
        if len(self.root.keys) == 0 and not self.root.leaf:
            self._log(
                "La raíz se quedó sin claves tras la operación; su único hijo "
                "pasa a ser la nueva raíz y el árbol reduce su altura en uno."
            )
            self.root = self.root.children[0]
        self._record(f"Eliminación de {k}", before=before)

    def _contains(self, x, k):
        i = 0
        while i < len(x.keys) and k > x.keys[i]:
            i += 1
        if i < len(x.keys) and x.keys[i] == k:
            return True
        if x.leaf:
            return False
        return self._contains(x.children[i], k)

    def _get_pred(self, node):
        while not node.leaf:
            node = node.children[-1]
        return node.keys[-1]

    def _get_succ(self, node):
        while not node.leaf:
            node = node.children[0]
        return node.keys[0]

    def _merge(self, x, i):
        t = self.t
        y = x.children[i]
        z = x.children[i + 1]
        sep = x.keys.pop(i)
        self._log(
            f"Se fusionan (COALESCE) el nodo {y.keys} con {z.keys}: la clave "
            f"separadora {sep} baja del padre y se ubica entre ambos, formando "
            f"un único nodo con {len(y.keys)+len(z.keys)+1} claves "
            f"(≤ 2t-1 = {2*t-1}, válido)."
        )
        y.keys.append(sep)
        y.keys.extend(z.keys)
        if not y.leaf:
            y.children.extend(z.children)
        x.children.pop(i + 1)

    def _borrow_from_left(self, x, i):
        child = x.children[i]
        sib = x.children[i - 1]
        self._touched.add(x.keys[i - 1])
        self._touched.add(sib.keys[-1])
        self._log(
            f"El hermano izquierdo (claves {sib.keys}) tiene claves de sobra "
            f"(≥ t={self.t}). Se toma PRESTADO: la clave separadora del padre "
            f"({x.keys[i-1]}) baja al hijo, y la última clave del hermano "
            f"({sib.keys[-1]}) sube a ocupar el lugar del padre."
        )
        child.keys.insert(0, x.keys[i - 1])
        if not child.leaf:
            child.children.insert(0, sib.children.pop())
        x.keys[i - 1] = sib.keys.pop()

    def _borrow_from_right(self, x, i):
        child = x.children[i]
        sib = x.children[i + 1]
        self._touched.add(x.keys[i])
        self._touched.add(sib.keys[0])
        self._log(
            f"El hermano derecho (claves {sib.keys}) tiene claves de sobra "
            f"(≥ t={self.t}). Se toma PRESTADO: la clave separadora del padre "
            f"({x.keys[i]}) baja al hijo, y la primera clave del hermano "
            f"({sib.keys[0]}) sube a ocupar el lugar del padre."
        )
        child.keys.append(x.keys[i])
        if not child.leaf:
            child.children.append(sib.children.pop(0))
        x.keys[i] = sib.keys.pop(0)

    def _delete(self, x, k):
        t = self.t
        i = 0
        while i < len(x.keys) and k > x.keys[i]:
            i += 1
        if i < len(x.keys) and x.keys[i] == k:
            if x.leaf:
                self._log(
                    f"La clave {k} se encontró en un nodo HOJA {x.keys} "
                    f"(caso 1: eliminación directa)."
                )
                x.keys.pop(i)
            else:
                y = x.children[i]
                z = x.children[i + 1]
                self._log(
                    f"La clave {k} se encontró en un nodo INTERNO {x.keys} "
                    f"(caso 2: hay que reemplazarla antes de quitarla)."
                )
                if len(y.keys) >= t:
                    pred = self._get_pred(y)
                    self._touched.add(pred)
                    self._log(
                        f"El hijo izquierdo tiene {len(y.keys)} ≥ t={t} "
                        f"claves, así que se usa su predecesor {pred} (la "
                        f"clave más grande del subárbol izquierdo) para "
                        f"reemplazar a {k} (caso 2a)."
                    )
                    x.keys[i] = pred
                    self._delete(y, pred)
                elif len(z.keys) >= t:
                    succ = self._get_succ(z)
                    self._touched.add(succ)
                    self._log(
                        f"El hijo derecho tiene {len(z.keys)} ≥ t={t} "
                        f"claves, así que se usa su sucesor {succ} (la clave "
                        f"más pequeña del subárbol derecho) para reemplazar "
                        f"a {k} (caso 2b)."
                    )
                    x.keys[i] = succ
                    self._delete(z, succ)
                else:
                    self._log(
                        f"Ni el hijo izquierdo ({y.keys}) ni el derecho "
                        f"({z.keys}) tienen al menos t={t} claves (ambos "
                        f"tienen t-1={t-1}); se fusionan junto con {k} en un "
                        f"solo nodo (caso 2c) y se elimina {k} de él."
                    )
                    self._merge(x, i)
                    self._delete(y, k)
        else:
            if x.leaf:
                return
            child = x.children[i]
            self._log(
                f"La clave {k} no está en el nodo actual {x.keys}; se debe "
                f"descender al hijo en la posición {i} (claves {child.keys})."
            )
            if len(child.keys) == t - 1:
                self._log(
                    f"Ese hijo tiene solo t-1={t-1} claves, el mínimo "
                    f"permitido: antes de bajar hay que reforzarlo (caso 3) "
                    f"para garantizar que nunca se descienda a un nodo en el "
                    f"límite mínimo."
                )
                left = x.children[i - 1] if i > 0 else None
                right = x.children[i + 1] if i < len(x.children) - 1 else None
                if left and len(left.keys) >= t:
                    self._borrow_from_left(x, i)
                elif right and len(right.keys) >= t:
                    self._borrow_from_right(x, i)
                elif left:
                    self._merge(x, i - 1)
                    i -= 1
                else:
                    self._merge(x, i)
            self._delete(x.children[i], k)