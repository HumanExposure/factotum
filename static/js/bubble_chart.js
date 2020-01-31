var pucColors = new Map([
    ["Arts and crafts/Office supplies", "#0079B0"],
    ["Cleaning products and household care", "#FF7B2E"],
    ["Electronics/small appliances", "#009C3A"],
    ["Home maintenance", "#E42A32"],
    ["Landscape/Yard", "#946BB9"],
    ["Personal care", "#92564E"],
    ["Pesticides", "#EC7ABF"],
    ["Pet care", "#7E7E7E"],
    ["Sports equipment", "#BFB83C"],
    ["Vehicle", "#00BDCC"]
]);

// Gets area from radius
function getArea(r) {
    return Math.PI * Math.pow(r, 2);
}

// Gets radius from area
function getRadius(a) {
    return Math.sqrt(a / Math.PI);
}

// Sets area to ((total product)/(children product))*(packed child area)
// radius is increased by padding
function setRadiusFromChildren(node, padding) {
    d3v5.packSiblings(node.children);
    node.r = getRadius(
        (node.value / (node.value -
            (node.data.value ? node.data.value.num_products : 0))) *
            getArea(d3v5.packEnclose(node.children).r)
    ) + padding;
}

// Sets area to ((total product)/(sibling total product count))*(sibling area)
function setRadiusFromSiblings(node, padding) {
    var ancestors = node.ancestors()
    var root = ancestors[ancestors.length - 1]
    var sibling = root.descendants().find(x => x.depth == node.depth && x.children);
    node.r = getRadius((node.value / sibling.value) * getArea(sibling.r - padding)) + padding;
}

function translateChild(node) {
    var parent = node.parent;
    if (parent) {
        node.x += parent.x;
        node.y += parent.y;
    }
}

function nestedBubbleChart(width, height, fixed, dataurl) {
    d3v5.json(dataurl)
        .then(function(data) {
            var size = Math.min(width, height)
            // load JSON into hierarchy data structure
            // compute cumulative product count
            // sort by cumulative product count
            var root = d3v5
                .hierarchy(data)
                .sum(d => (d.value ? d.value.num_products : 0))
                .sort((a, b) => b.value - a.value);

            // center our root
            root.x = 0;
            root.y = 0;

            // set the color and opacity for each node
            root.children.forEach(gencat_node => {
                // color is based on gen_cat name
                let color = pucColors.get(gencat_node.data.name);
                gencat_node.descendants().forEach(node => {
                    // level 1 pucs are `color`, half opacity
                    // level 2 pucs are `color`, full opacity
                    // level 3 pucs are white, full opacity
                    node.color = node.depth == 3 ? "white" : color;
                    node.opacity = node.depth == 1 ? 0.5 : 1;
                });
            });

            // find our most granular PUC level as foundation for sizing
            var deepest_level = Math.max(...root.leaves().map(x => x.depth));

            // set area to product count for every deepest level PUC
            root.leaves().forEach(node => {
                if (node.depth == deepest_level) {
                    node.r = getRadius(node.value);
                }
            });

            // Add padding to parent PUCs
            var padding = 0;

            // set area of parent PUCs with children
            var current_level = deepest_level - 1;
            while (current_level >= 0) {
                root.descendants().forEach(node => {
                    if (node.depth == current_level && node.children) {
                        setRadiusFromChildren(node, padding);
                    }
                });
                root.descendants().forEach(node => {
                    if (node.depth == current_level && !node.children) {
                        setRadiusFromSiblings(node, padding);
                    }
                });
                current_level--;
            }

            // move circles
            root.eachBefore(translateChild);

            let focus = root;
            let view;

            const svg = d3v5
                .select("#nestedcircles")
                .attr(
                    "viewBox",
                    `-${size / 2} -${size / 2} ${size} ${size}`
                )
                .style("display", "block")
                // .style("position", "fixed")
                .style("background", "#eae9e0")
                .style("cursor", "pointer")
                .on("click", () => zoom(root));
            if (fixed === true){
                svg.style("position", "fixed")
            }

           const node = svg
                .append("g")
                .selectAll("circle")
                .data(root.descendants().slice(1))
                .join("circle")
                .attr("class", "bubble")
                .attr("fill", d => d.color)
                .attr("opacity", d => d.opacity)
                .attr("pointer-events", d => (!d.children ? "none" : null))
                .on("mouseover", function() {
                    d3v5.select(this).attr("stroke", "#000");
                })
                .on("mouseout", function() {
                    d3v5.select(this).attr("stroke", null);
                })
                .on(
                    "click",
                    d => focus !== d && (zoom(d), d3v5.event.stopPropagation())
                );

            const label = svg
                .append("g")
                .attr("pointer-events", "none")
                .attr("text-anchor", "middle")
                .selectAll("text")
                .data(root.descendants())
                .join("text")
                .style("font", d => (d.parent === root ? "0px sans-serif" : "14px sans-serif"))
                .style("fill-opacity", d => (d.parent === focus ? 1 : 0))
                .style("display", d => (d.parent === root ? "inline" : "none"))
                // Display the name with the cumulative count
                .text(d => d.data.name + " (" + d.value + ")");

            zoomTo([root.x, root.y, root.r * 2]);

            function zoomTo(v) {
                const k = size / v[2];

                view = v;

                label.attr(
                    "transform",
                    d => `translate(${(d.x - v[0]) * k},${(d.y - v[1]) * k})`
                );
                node.attr(
                    "transform",
                    d => `translate(${(d.x - v[0]) * k},${(d.y - v[1]) * k})`
                );
                node.attr("r", d => d.r * k);
            }

            function zoom(d) {
                const focus0 = focus;

                focus = d;

                const transition = svg
                    .transition()
                    .duration(d3v5.event.altKey ? 7500 : 750)
                    .tween("zoom", d => {
                        const i = d3v5.interpolateZoom(view, [
                            focus.x,
                            focus.y,
                            focus.r * 2
                        ]);
                        return t => zoomTo(i(t));
                    });

                label
                    .filter(function(d) {
                        return (
                            d.parent === focus ||
                            this.style.display === "inline"
                        );
                    })
                    .transition(transition)
                    .style("font", d => (d.parent === root ? "0px sans-serif" : "14px sans-serif"))
                    .style("fill-opacity", d => (d.parent === focus ? 1 : 0))
                    .on("start", function(d) {
                        if (d.parent === focus) this.style.display = "inline";
                    })
                    .on("end", function(d) {
                        if (d.parent !== focus) this.style.display = "none";
                    });
            }

            return svg.node();
        })
        .catch(console.log.bind(console));
}
