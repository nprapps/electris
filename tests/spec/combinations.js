describe("Combinations math", function() {
    beforeEach(function() {
    });

    it("Should find combinations", function() {
        var superset = ["a", "b", "c"];
        var expected_combos = [["a", "b"], ["a", "c"], ["b", "c"], ["a", "b", "c"]];

        var combos = combinations(superset);

        expect(combos).toEqual(expected_combos);
    });

    it("Should find more combinations", function() {
        var superset = ["a", "b", "c", "d"];
        var expected_combos = [["a", "b"], ["a", "c"], ["a", "d"], ["b", "c"], ["b", "d"], ["c", "d"], ["a", "b", "c"], ["a", "b", "d"], ["a", "c", "d"], ["b", "c", "d"],  ["a", "b", "c", "d"]];

        var combos = combinations(superset);

        expect(combos).toEqual(expected_combos);
    });
});
